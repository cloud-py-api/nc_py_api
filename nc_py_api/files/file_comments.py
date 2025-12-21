"""Nextcloud API for working with file comments."""

import dataclasses
import datetime
from xml.etree import ElementTree

from .._exceptions import check_error
from .._misc import check_capabilities, nc_iso_time_to_datetime, require_capabilities
from .._session import AsyncNcSessionBasic, NcSessionBasic
from . import FsNode
from ._files import _webdav_response_to_records


@dataclasses.dataclass
class FileComment:
    """Class representing one file comment."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def comment_id(self) -> int:
        """Unique identifier of the comment."""
        return int(self._raw_data.get("oc:id", 0))

    @property
    def message(self) -> str:
        """Comment message content."""
        return self._raw_data.get("oc:message", "")

    @property
    def actor_id(self) -> str:
        """ID of the user who created the comment."""
        return self._raw_data.get("oc:actorId", "")

    @property
    def actor_type(self) -> str:
        """Type of actor (e.g., 'users', 'guests')."""
        return self._raw_data.get("oc:actorType", "")

    @property
    def creation_datetime(self) -> datetime.datetime:
        """Creation date and time of the comment."""
        dt_str = self._raw_data.get("oc:creationDateTime", "")
        if dt_str:
            return nc_iso_time_to_datetime(dt_str)
        return datetime.datetime(1970, 1, 1)

    @property
    def parent_id(self) -> int:
        """ID of the parent comment (0 for top-level comments)."""
        return int(self._raw_data.get("oc:parentId", 0))

    @property
    def topmost_parent_id(self) -> int:
        """ID of the topmost parent comment."""
        return int(self._raw_data.get("oc:topmostParentId", 0))

    @property
    def children_count(self) -> int:
        """Number of child comments."""
        return int(self._raw_data.get("oc:childrenCount", 0))

    @property
    def object_id(self) -> int:
        """ID of the file this comment belongs to."""
        return int(self._raw_data.get("oc:objectId", 0))

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} id={self.comment_id}, actor={self.actor_id}, message={self.message[:30]}...>"
        )


def _build_comment_propfind_request() -> ElementTree.Element:
    """Build PROPFIND request for listing comments."""
    root = ElementTree.Element(
        "d:propfind",
        attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns"},
    )
    prop = ElementTree.SubElement(root, "d:prop")
    ElementTree.SubElement(prop, "oc:id")
    ElementTree.SubElement(prop, "oc:message")
    ElementTree.SubElement(prop, "oc:actorId")
    ElementTree.SubElement(prop, "oc:actorType")
    ElementTree.SubElement(prop, "oc:creationDateTime")
    ElementTree.SubElement(prop, "oc:parentId")
    ElementTree.SubElement(prop, "oc:topmostParentId")
    ElementTree.SubElement(prop, "oc:childrenCount")
    ElementTree.SubElement(prop, "oc:objectId")
    return root


def _build_comment_create_request(message: str) -> ElementTree.Element:
    """Build POST request body for creating a comment."""
    root = ElementTree.Element(
        "oc:comment",
        attrib={"xmlns:oc": "http://owncloud.org/ns"},
    )
    ElementTree.SubElement(root, "oc:message").text = message
    return root


def _parse_comments_response(response) -> list[FileComment]:
    """Parse WebDAV response containing comments."""
    comments = []
    records = _webdav_response_to_records(response, "comments")
    for record in records:
        # Try to get comment from propstat (PROPFIND response)
        prop_stat = record.get("d:propstat", {})
        if prop_stat:
            if str(prop_stat.get("d:status", "")).find("200 OK") == -1:
                continue
            prop = prop_stat.get("d:prop", {})
            comment_data = prop.get("oc:comment", {})
            if comment_data:
                comments.append(FileComment(comment_data))
        # Also check if comment is directly in record (some response formats)
        elif "oc:comment" in record:
            comments.append(FileComment(record["oc:comment"]))
    return comments


def _element_tree_as_str(element: ElementTree.Element) -> str:
    """Convert ElementTree element to XML string."""
    return ElementTree.tostring(element, encoding="unicode", xml_declaration=True)


class _FileCommentsAPI:
    """Class providing File Comments API on the Nextcloud server."""

    _ep_base: str = "/remote.php/dav/comments/files"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports file comments, False otherwise."""
        return not check_capabilities("files", self._session.capabilities)

    def get_list(self, file_id: int | str | FsNode, limit: int | None = None, offset: int = 0) -> list[FileComment]:
        """Returns a list of comments for a file.

        :param file_id: File ID, file_id string, or FsNode object.
        :param limit: Maximum number of comments to return.
        :param offset: Offset for pagination.
        """
        require_capabilities("files", self._session.capabilities)
        object_id = self._get_object_id(file_id)
        root = _build_comment_propfind_request()
        response = self._session.adapter_dav.request(
            "PROPFIND", f"{self._ep_base}/{object_id}", data=_element_tree_as_str(root)
        )
        comments = _parse_comments_response(response)
        # Apply pagination if needed
        if limit is not None:
            comments = comments[offset : offset + limit]
        elif offset > 0:
            comments = comments[offset:]
        return comments

    def create(self, file_id: int | str | FsNode, message: str) -> FileComment:
        """Creates a new comment on a file.

        :param file_id: File ID, file_id string, or FsNode object.
        :param message: Comment message content.
        :returns: FileComment object representing the created comment.
        """
        require_capabilities("files", self._session.capabilities)
        if not message:
            raise ValueError("`message` parameter cannot be empty")
        object_id = self._get_object_id(file_id)
        root = _build_comment_create_request(message)
        response = self._session.adapter_dav.request(
            "POST",
            f"{self._ep_base}/{object_id}",
            data=_element_tree_as_str(root),
            headers={"Content-Type": "text/xml"},
        )
        check_error(response, info=f"create_comment({object_id})")
        # After creation, fetch the comment to return it
        comments = self.get_list(object_id, limit=1)
        if comments:
            return comments[-1]
        raise ValueError("Comment was created but could not be retrieved.")

    def update(self, file_id: int | str | FsNode, comment_id: int, message: str) -> None:
        """Updates a comment on a file.

        :param file_id: File ID, file_id string, or FsNode object.
        :param comment_id: ID of the comment to update.
        :param message: New comment message content.
        """
        require_capabilities("files", self._session.capabilities)
        if not message:
            raise ValueError("`message` parameter cannot be empty")
        object_id = self._get_object_id(file_id)
        root = ElementTree.Element(
            "d:propertyupdate",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns"},
        )
        prop_set = ElementTree.SubElement(root, "d:set")
        prop = ElementTree.SubElement(prop_set, "d:prop")
        ElementTree.SubElement(prop, "oc:message").text = message
        response = self._session.adapter_dav.request(
            "PROPPATCH", f"{self._ep_base}/{object_id}/{comment_id}", data=_element_tree_as_str(root)
        )
        check_error(response)

    def delete(self, file_id: int | str | FsNode, comment_id: int) -> None:
        """Deletes a comment from a file.

        :param file_id: File ID, file_id string, or FsNode object.
        :param comment_id: ID of the comment to delete.
        """
        require_capabilities("files", self._session.capabilities)
        object_id = self._get_object_id(file_id)
        response = self._session.adapter_dav.delete(f"{self._ep_base}/{object_id}/{comment_id}")
        check_error(response)

    def _get_object_id(self, file_id: int | str | FsNode) -> str:
        """Extract object ID from various input types."""
        if isinstance(file_id, FsNode):
            # Extract numeric file ID from file_id string (format: "instance_id:fileid")
            file_id_str = file_id.file_id
            if ":" in file_id_str:
                return file_id_str.split(":")[-1]
            return file_id_str
        return str(file_id)


class _AsyncFileCommentsAPI:
    """Class provides async File Comments API on the Nextcloud server."""

    _ep_base: str = "/remote.php/dav/comments/files"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports file comments, False otherwise."""
        return not check_capabilities("files", await self._session.capabilities)

    async def get_list(
        self, file_id: int | str | FsNode, limit: int | None = None, offset: int = 0
    ) -> list[FileComment]:
        """Returns a list of comments for a file.

        :param file_id: File ID, file_id string, or FsNode object.
        :param limit: Maximum number of comments to return.
        :param offset: Offset for pagination.
        """
        require_capabilities("files", await self._session.capabilities)
        object_id = self._get_object_id(file_id)
        root = _build_comment_propfind_request()
        response = await self._session.adapter_dav.request(
            "PROPFIND", f"{self._ep_base}/{object_id}", data=_element_tree_as_str(root)
        )
        comments = _parse_comments_response(response)
        # Apply pagination if needed
        if limit is not None:
            comments = comments[offset : offset + limit]
        elif offset > 0:
            comments = comments[offset:]
        return comments

    async def create(self, file_id: int | str | FsNode, message: str) -> FileComment:
        """Creates a new comment on a file.

        :param file_id: File ID, file_id string, or FsNode object.
        :param message: Comment message content.
        :returns: FileComment object representing the created comment.
        """
        require_capabilities("files", await self._session.capabilities)
        if not message:
            raise ValueError("`message` parameter cannot be empty")
        object_id = self._get_object_id(file_id)
        root = _build_comment_create_request(message)
        response = await self._session.adapter_dav.request(
            "POST",
            f"{self._ep_base}/{object_id}",
            data=_element_tree_as_str(root),
            headers={"Content-Type": "text/xml"},
        )
        check_error(response, info=f"create_comment({object_id})")
        # After creation, fetch the comment to return it
        comments = await self.get_list(object_id, limit=1)
        if comments:
            return comments[-1]
        raise ValueError("Comment was created but could not be retrieved.")

    async def update(self, file_id: int | str | FsNode, comment_id: int, message: str) -> None:
        """Updates a comment on a file.

        :param file_id: File ID, file_id string, or FsNode object.
        :param comment_id: ID of the comment to update.
        :param message: New comment message content.
        """
        require_capabilities("files", await self._session.capabilities)
        if not message:
            raise ValueError("`message` parameter cannot be empty")
        object_id = self._get_object_id(file_id)
        root = ElementTree.Element(
            "d:propertyupdate",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns"},
        )
        prop_set = ElementTree.SubElement(root, "d:set")
        prop = ElementTree.SubElement(prop_set, "d:prop")
        ElementTree.SubElement(prop, "oc:message").text = message
        response = await self._session.adapter_dav.request(
            "PROPPATCH", f"{self._ep_base}/{object_id}/{comment_id}", data=_element_tree_as_str(root)
        )
        check_error(response)

    async def delete(self, file_id: int | str | FsNode, comment_id: int) -> None:
        """Deletes a comment from a file.

        :param file_id: File ID, file_id string, or FsNode object.
        :param comment_id: ID of the comment to delete.
        """
        require_capabilities("files", await self._session.capabilities)
        object_id = self._get_object_id(file_id)
        response = await self._session.adapter_dav.delete(f"{self._ep_base}/{object_id}/{comment_id}")
        check_error(response)

    def _get_object_id(self, file_id: int | str | FsNode) -> str:
        """Extract object ID from various input types."""
        if isinstance(file_id, FsNode):
            # Extract numeric file ID from file_id string (format: "instance_id:fileid")
            file_id_str = file_id.file_id
            if ":" in file_id_str:
                return file_id_str.split(":")[-1]
            return file_id_str
        return str(file_id)
