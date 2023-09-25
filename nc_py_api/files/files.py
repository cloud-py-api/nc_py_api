"""Nextcloud API for working with the file system."""

import builtins
import enum
import os
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from typing import Optional, Union
from urllib.parse import unquote
from xml.etree import ElementTree

import xmltodict
from httpx import Response

from .._exceptions import NextcloudException, NextcloudExceptionNotFound, check_error
from .._misc import clear_from_params_empty, random_string, require_capabilities
from .._session import NcSessionBasic
from . import FsNode, SystemTag
from .sharing import _FilesSharingAPI

PROPFIND_PROPERTIES = [
    "d:resourcetype",
    "d:getlastmodified",
    "d:getcontentlength",
    "d:getcontenttype",
    "d:getetag",
    "oc:size",
    "oc:id",
    "oc:fileid",
    "oc:downloadURL",
    "oc:dDC",
    "oc:permissions",
    "oc:checksums",
    "oc:share-types",
    "oc:favorite",
    "nc:is-encrypted",
    "nc:lock",
    "nc:lock-owner-displayname",
    "nc:lock-owner",
    "nc:lock-owner-type",
    "nc:lock-owner-editor",
    "nc:lock-time",
    "nc:lock-timeout",
]

SEARCH_PROPERTIES_MAP = {
    "name": "d:displayname",  # like, eq
    "mime": "d:getcontenttype",  # like, eq
    "last_modified": "d:getlastmodified",  # gt, eq, lt
    "size": "oc:size",  # gt, gte, eq, lt
    "favorite": "oc:favorite",  # eq
    "fileid": "oc:fileid",  # eq
}


class PropFindType(enum.IntEnum):
    """Internal enum types for ``_listdir`` and ``_lf_parse_webdav_records`` methods."""

    DEFAULT = 0
    TRASHBIN = 1
    VERSIONS_FILEID = 2
    VERSIONS_FILE_ID = 3


class FilesAPI:
    """Class that encapsulates the file system and file sharing functionality."""

    sharing: _FilesSharingAPI
    """API for managing Files Shares"""

    def __init__(self, session: NcSessionBasic):
        self._session = session
        self.sharing = _FilesSharingAPI(session)

    def listdir(self, path: Union[str, FsNode] = "", depth: int = 1, exclude_self=True) -> list[FsNode]:
        """Returns a list of all entries in the specified directory.

        :param path: path to the directory to get the list.
        :param depth: how many directory levels should be included in output. Default = **1** (only specified directory)
        :param exclude_self: boolean value indicating whether the `path` itself should be excluded from the list or not.
            Default = **True**.
        """
        if exclude_self and not depth:
            raise ValueError("Wrong input parameters, query will return nothing.")
        properties = PROPFIND_PROPERTIES
        path = path.user_path if isinstance(path, FsNode) else path
        return self._listdir(self._session.user, path, properties=properties, depth=depth, exclude_self=exclude_self)

    def by_id(self, file_id: Union[int, str, FsNode]) -> Optional[FsNode]:
        """Returns :py:class:`~nc_py_api.files.FsNode` by file_id if any.

        :param file_id: can be full file ID with Nextcloud instance ID or only clear file ID.
        """
        file_id = file_id.file_id if isinstance(file_id, FsNode) else file_id
        result = self.find(req=["eq", "fileid", file_id])
        return result[0] if result else None

    def by_path(self, path: Union[str, FsNode]) -> Optional[FsNode]:
        """Returns :py:class:`~nc_py_api.files.FsNode` by exact path if any."""
        path = path.user_path if isinstance(path, FsNode) else path
        result = self.listdir(path, depth=0, exclude_self=False)
        return result[0] if result else None

    def find(self, req: list, path: Union[str, FsNode] = "") -> list[FsNode]:
        """Searches a directory for a file or subdirectory with a name.

        :param req: list of conditions to search for. Detailed description here...
        :param path: path where to search from. Default = **""**.
        """
        # `req` possible keys: "name", "mime", "last_modified", "size", "favorite", "fileid"
        path = path.user_path if isinstance(path, FsNode) else path
        root = ElementTree.Element(
            "d:searchrequest",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
        )
        xml_search = ElementTree.SubElement(root, "d:basicsearch")
        xml_select_prop = ElementTree.SubElement(ElementTree.SubElement(xml_search, "d:select"), "d:prop")
        for i in PROPFIND_PROPERTIES:
            ElementTree.SubElement(xml_select_prop, i)
        xml_from_scope = ElementTree.SubElement(ElementTree.SubElement(xml_search, "d:from"), "d:scope")
        href = f"/files/{self._session.user}/{path.removeprefix('/')}"
        ElementTree.SubElement(xml_from_scope, "d:href").text = href
        ElementTree.SubElement(xml_from_scope, "d:depth").text = "infinity"
        xml_where = ElementTree.SubElement(xml_search, "d:where")
        self._build_search_req(xml_where, req)

        headers = {"Content-Type": "text/xml"}
        webdav_response = self._session.dav("SEARCH", "", data=self._element_tree_as_str(root), headers=headers)
        request_info = f"find: {self._session.user}, {req}, {path}"
        return self._lf_parse_webdav_response(webdav_response, request_info)

    def download(self, path: Union[str, FsNode]) -> bytes:
        """Downloads and returns the content of a file.

        :param path: path to download file.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        response = self._session.dav("GET", self._dav_get_obj_path(self._session.user, path))
        check_error(response.status_code, f"download: user={self._session.user}, path={path}")
        return response.content

    def download2stream(self, path: Union[str, FsNode], fp, **kwargs) -> None:
        """Downloads file to the given `fp` object.

        :param path: path to download file.
        :param fp: filename (string), pathlib.Path object or a file object.
            The object must implement the ``file.write`` method and be able to write binary data.
        :param kwargs: **chunk_size** an int value specifying chunk size to write. Default = **5Mb**
        """
        path = path.user_path if isinstance(path, FsNode) else path
        if isinstance(fp, (str, Path)):
            with builtins.open(fp, "wb") as f:
                self.__download2stream(path, f, **kwargs)
        elif hasattr(fp, "write"):
            self.__download2stream(path, fp, **kwargs)
        else:
            raise TypeError("`fp` must be a path to file or an object with `write` method.")

    def download_directory_as_zip(
        self, path: Union[str, FsNode], local_path: Union[str, Path, None] = None, **kwargs
    ) -> Path:
        """Downloads a remote directory as zip archive.

        :param path: path to directory to download.
        :param local_path: relative or absolute file path to save zip file.
        :returns: Path to the saved zip archive.

        .. note:: This works only for directories, you should not use this to download a file.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        with self._session.get_stream(
            "/index.php/apps/files/ajax/download.php", params={"dir": path}
        ) as response:  # type: ignore
            self._session.response_headers = response.headers
            check_error(response.status_code, f"download_directory_as_zip: user={self._session.user}, path={path}")
            result_path = local_path if local_path else os.path.basename(path)
            with open(
                result_path,
                "wb",
            ) as fp:
                for data_chunk in response.iter_raw(chunk_size=kwargs.get("chunk_size", 5 * 1024 * 1024)):
                    fp.write(data_chunk)
        return Path(result_path)

    def upload(self, path: Union[str, FsNode], content: Union[bytes, str]) -> FsNode:
        """Creates a file with the specified content at the specified path.

        :param path: file's upload path.
        :param content: content to create the file. If it is a string, it will be encoded into bytes using UTF-8.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        full_path = self._dav_get_obj_path(self._session.user, path)
        response = self._session.dav("PUT", full_path, data=content)
        check_error(response.status_code, f"upload: user={self._session.user}, path={path}, size={len(content)}")
        return FsNode(full_path.strip("/"), **self.__get_etag_fileid_from_response(response))

    def upload_stream(self, path: Union[str, FsNode], fp, **kwargs) -> FsNode:
        """Creates a file with content provided by `fp` object at the specified path.

        :param path: file's upload path.
        :param fp: filename (string), pathlib.Path object or a file object.
            The object must implement the ``file.read`` method providing data with str or bytes type.
        :param kwargs: **chunk_size** an int value specifying chunk size to read. Default = **5Mb**
        """
        path = path.user_path if isinstance(path, FsNode) else path
        chunk_size = kwargs.get("chunk_size", 5 * 1024 * 1024)
        if isinstance(fp, (str, Path)):
            with builtins.open(fp, "rb") as f:
                return self.__upload_stream(path, f, chunk_size)
        elif hasattr(fp, "read"):
            return self.__upload_stream(path, fp, chunk_size)
        else:
            raise TypeError("`fp` must be a path to file or an object with `read` method.")

    def mkdir(self, path: Union[str, FsNode]) -> FsNode:
        """Creates a new directory.

        :param path: path of the directory to be created.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        full_path = self._dav_get_obj_path(self._session.user, path)
        response = self._session.dav("MKCOL", full_path)
        check_error(response.status_code, f"mkdir: user={self._session.user}, path={path}")
        full_path += "/" if not full_path.endswith("/") else ""
        return FsNode(full_path.lstrip("/"), **self.__get_etag_fileid_from_response(response))

    def makedirs(self, path: Union[str, FsNode], exist_ok=False) -> Optional[FsNode]:
        """Creates a new directory and subdirectories.

        :param path: path of the directories to be created.
        :param exist_ok: ignore error if any of pathname components already exists.
        :returns: `FsNode` if directory was created or ``None`` if it was already created.
        """
        _path = ""
        path = path.user_path if isinstance(path, FsNode) else path
        path = path.lstrip("/")
        result = None
        for i in Path(path).parts:
            _path = os.path.join(_path, i)
            if not exist_ok:
                result = self.mkdir(_path)
            else:
                try:
                    result = self.mkdir(_path)
                except NextcloudException as e:
                    if e.status_code != 405:
                        raise e from None
        return result

    def delete(self, path: Union[str, FsNode], not_fail=False) -> None:
        """Deletes a file/directory (moves to trash if trash is enabled).

        :param path: path to delete.
        :param not_fail: if set to ``True`` and the object is not found, it does not raise an exception.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        response = self._session.dav("DELETE", self._dav_get_obj_path(self._session.user, path))
        if response.status_code == 404 and not_fail:
            return
        check_error(response.status_code, f"delete: user={self._session.user}, path={path}")

    def move(self, path_src: Union[str, FsNode], path_dest: Union[str, FsNode], overwrite=False) -> FsNode:
        """Moves an existing file or a directory.

        :param path_src: path of an existing file/directory.
        :param path_dest: name of the new one.
        :param overwrite: if ``True`` and the destination object already exists, it gets overwritten.
            Default = **False**.
        """
        path_src = path_src.user_path if isinstance(path_src, FsNode) else path_src
        full_dest_path = self._dav_get_obj_path(
            self._session.user, path_dest.user_path if isinstance(path_dest, FsNode) else path_dest
        )
        dest = self._session.cfg.dav_endpoint + full_dest_path
        headers = {"Destination": dest, "Overwrite": "T" if overwrite else "F"}
        response = self._session.dav(
            "MOVE",
            self._dav_get_obj_path(self._session.user, path_src),
            headers=headers,
        )
        check_error(response.status_code, f"move: user={self._session.user}, src={path_src}, dest={dest}, {overwrite}")
        return self.find(req=["eq", "fileid", response.headers["OC-FileId"]])[0]

    def copy(self, path_src: Union[str, FsNode], path_dest: Union[str, FsNode], overwrite=False) -> FsNode:
        """Copies an existing file/directory.

        :param path_src: path of an existing file/directory.
        :param path_dest: name of the new one.
        :param overwrite: if ``True`` and the destination object already exists, it gets overwritten.
            Default = **False**.
        """
        path_src = path_src.user_path if isinstance(path_src, FsNode) else path_src
        full_dest_path = self._dav_get_obj_path(
            self._session.user, path_dest.user_path if isinstance(path_dest, FsNode) else path_dest
        )
        dest = self._session.cfg.dav_endpoint + full_dest_path
        headers = {"Destination": dest, "Overwrite": "T" if overwrite else "F"}
        response = self._session.dav(
            "COPY",
            self._dav_get_obj_path(self._session.user, path_src),
            headers=headers,
        )
        check_error(response.status_code, f"copy: user={self._session.user}, src={path_src}, dest={dest}, {overwrite}")
        return self.find(req=["eq", "fileid", response.headers["OC-FileId"]])[0]

    def list_by_criteria(
        self, properties: Optional[list[str]] = None, tags: Optional[list[Union[int, SystemTag]]] = None
    ) -> list[FsNode]:
        """Returns a list of all files/directories for the current user filtered by the specified values.

        :param properties: List of ``properties`` that should have been set for the file.
            Supported values: **favorite**
        :param tags: List of ``tags ids`` or ``SystemTag`` that should have been set for the file.
        """
        if not properties and not tags:
            raise ValueError("Either specify 'properties' or 'tags' to filter results.")
        root = ElementTree.Element(
            "oc:filter-files",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
        )
        prop = ElementTree.SubElement(root, "d:prop")
        for i in PROPFIND_PROPERTIES:
            ElementTree.SubElement(prop, i)
        xml_filter_rules = ElementTree.SubElement(root, "oc:filter-rules")
        if properties and "favorite" in properties:
            ElementTree.SubElement(xml_filter_rules, "oc:favorite").text = "1"
        if tags:
            for v in tags:
                tag_id = v.tag_id if isinstance(v, SystemTag) else v
                ElementTree.SubElement(xml_filter_rules, "oc:systemtag").text = str(tag_id)
        webdav_response = self._session.dav(
            "REPORT", self._dav_get_obj_path(self._session.user), data=self._element_tree_as_str(root)
        )
        request_info = f"list_files_by_criteria: {self._session.user}"
        check_error(webdav_response.status_code, request_info)
        return self._lf_parse_webdav_response(webdav_response, request_info)

    def setfav(self, path: Union[str, FsNode], value: Union[int, bool]) -> None:
        """Sets or unsets favourite flag for specific file.

        :param path: path to the object to set the state.
        :param value: value to set for the ``favourite`` state.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        root = ElementTree.Element(
            "d:propertyupdate",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns"},
        )
        xml_set = ElementTree.SubElement(root, "d:set")
        xml_set_prop = ElementTree.SubElement(xml_set, "d:prop")
        ElementTree.SubElement(xml_set_prop, "oc:favorite").text = str(int(bool(value)))
        webdav_response = self._session.dav(
            "PROPPATCH", self._dav_get_obj_path(self._session.user, path), data=self._element_tree_as_str(root)
        )
        check_error(webdav_response.status_code, f"setfav: path={path}, value={value}")

    def trashbin_list(self) -> list[FsNode]:
        """Returns a list of all entries in the TrashBin."""
        properties = PROPFIND_PROPERTIES
        properties += ["nc:trashbin-filename", "nc:trashbin-original-location", "nc:trashbin-deletion-time"]
        return self._listdir(
            self._session.user, "", properties=properties, depth=1, exclude_self=False, prop_type=PropFindType.TRASHBIN
        )

    def trashbin_restore(self, path: Union[str, FsNode]) -> None:
        """Restore a file/directory from the TrashBin.

        :param path: path to delete, e.g., the ``user_path`` field from ``FsNode`` or the **FsNode** class itself.
        """
        restore_name = path.name if isinstance(path, FsNode) else path.split("/", maxsplit=1)[-1]
        path = path.user_path if isinstance(path, FsNode) else path

        dest = self._session.cfg.dav_endpoint + f"/trashbin/{self._session.user}/restore/{restore_name}"
        headers = {"Destination": dest}
        response = self._session.dav(
            "MOVE",
            path=f"/trashbin/{self._session.user}/{path}",
            headers=headers,
        )
        check_error(response.status_code, f"trashbin_restore: user={self._session.user}, src={path}, dest={dest}")

    def trashbin_delete(self, path: Union[str, FsNode], not_fail=False) -> None:
        """Deletes a file/directory permanently from the TrashBin.

        :param path: path to delete, e.g., the ``user_path`` field from ``FsNode`` or the **FsNode** class itself.
        :param not_fail: if set to ``True`` and the object is not found, it does not raise an exception.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        response = self._session.dav(method="DELETE", path=f"/trashbin/{self._session.user}/{path}")
        if response.status_code == 404 and not_fail:
            return
        check_error(response.status_code, f"delete_from_trashbin: user={self._session.user}, path={path}")

    def trashbin_cleanup(self) -> None:
        """Empties the TrashBin."""
        response = self._session.dav(method="DELETE", path=f"/trashbin/{self._session.user}/trash")
        check_error(response.status_code, f"trashbin_cleanup: user={self._session.user}")

    def get_versions(self, file_object: FsNode) -> list[FsNode]:
        """Returns a list of all file versions if any."""
        require_capabilities("files.versioning", self._session.capabilities)
        return self._listdir(
            self._session.user,
            str(file_object.info.fileid) if file_object.info.fileid else file_object.file_id,
            properties=PROPFIND_PROPERTIES,
            depth=1,
            exclude_self=False,
            prop_type=PropFindType.VERSIONS_FILEID if file_object.info.fileid else PropFindType.VERSIONS_FILE_ID,
        )

    def restore_version(self, file_object: FsNode) -> None:
        """Restore a file with specified version.

        :param file_object: The **FsNode** class from :py:meth:`~nc_py_api.files.files.FilesAPI.get_versions`.
        """
        require_capabilities("files.versioning", self._session.capabilities)
        dest = self._session.cfg.dav_endpoint + f"/versions/{self._session.user}/restore/{file_object.name}"
        headers = {"Destination": dest}
        response = self._session.dav(
            "MOVE",
            path=f"/versions/{self._session.user}/{file_object.user_path}",
            headers=headers,
        )
        check_error(response.status_code, f"restore_version: user={self._session.user}, src={file_object.user_path}")

    def list_tags(self) -> list[SystemTag]:
        """Returns list of the avalaible Tags."""
        root = ElementTree.Element(
            "d:propfind",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns"},
        )
        properties = ["oc:id", "oc:display-name", "oc:user-visible", "oc:user-assignable"]
        prop_element = ElementTree.SubElement(root, "d:prop")
        for i in properties:
            ElementTree.SubElement(prop_element, i)
        response = self._session.dav("PROPFIND", "/systemtags", self._element_tree_as_str(root))
        result = []
        records = self._webdav_response_to_records(response, "list_tags")
        for record in records:
            prop_stat = record["d:propstat"]
            if str(prop_stat.get("d:status", "")).find("200 OK") == -1:
                continue
            result.append(SystemTag(prop_stat["d:prop"]))
        return result

    def create_tag(self, name: str, user_visible: bool = True, user_assignable: bool = True) -> None:
        """Creates a new Tag.

        :param name: Name of the tag.
        :param user_visible: Should be Tag visible in the UI.
        :param user_assignable: Can Tag be assigned from the UI.
        """
        response = self._session.dav(
            "POST",
            path="/systemtags",
            json={
                "name": name,
                "userVisible": user_visible,
                "userAssignable": user_assignable,
            },
        )
        check_error(response.status_code, info=f"create_tag({name})")

    def update_tag(
        self,
        tag_id: Union[int, SystemTag],
        name: Optional[str] = None,
        user_visible: Optional[bool] = None,
        user_assignable: Optional[bool] = None,
    ) -> None:
        """Updates the Tag information."""
        tag_id = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        root = ElementTree.Element(
            "d:propertyupdate",
            attrib={
                "xmlns:d": "DAV:",
                "xmlns:oc": "http://owncloud.org/ns",
            },
        )
        properties = {
            "oc:display-name": name,
            "oc:user-visible": "true" if user_visible is True else "false" if user_visible is False else None,
            "oc:user-assignable": "true" if user_assignable is True else "false" if user_assignable is False else None,
        }
        clear_from_params_empty(list(properties.keys()), properties)
        if not properties:
            raise ValueError("No property specified to change.")
        xml_set = ElementTree.SubElement(root, "d:set")
        prop_element = ElementTree.SubElement(xml_set, "d:prop")
        for k, v in properties.items():
            ElementTree.SubElement(prop_element, k).text = v
        response = self._session.dav("PROPPATCH", f"/systemtags/{tag_id}", self._element_tree_as_str(root))
        check_error(response.status_code, info=f"update_tag({tag_id})")

    def delete_tag(self, tag_id: Union[int, SystemTag]) -> None:
        """Deletes the tag."""
        tag_id = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        response = self._session.dav("DELETE", f"/systemtags/{tag_id}")
        check_error(response.status_code, info=f"delete_tag({tag_id})")

    def tag_by_name(self, tag_name: str) -> SystemTag:
        """Returns Tag info by its name if found or ``None`` otherwise."""
        r = [i for i in self.list_tags() if i.display_name == tag_name]
        if not r:
            raise NextcloudExceptionNotFound(f"Tag with name='{tag_name}' not found.")
        return r[0]

    def assign_tag(self, file_id: Union[FsNode, int], tag_id: Union[SystemTag, int]) -> None:
        """Assigns Tag to a file/directory."""
        self._file_change_tag_state(file_id, tag_id, True)

    def unassign_tag(self, file_id: Union[FsNode, int], tag_id: Union[SystemTag, int]) -> None:
        """Removes Tag from a file/directory."""
        self._file_change_tag_state(file_id, tag_id, False)

    def _file_change_tag_state(
        self, file_id: Union[FsNode, int], tag_id: Union[SystemTag, int], tag_state: bool
    ) -> None:
        request = "PUT" if tag_state else "DELETE"
        fs_object = file_id.info.fileid if isinstance(file_id, FsNode) else file_id
        tag = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        response = self._session.dav(request, f"/systemtags-relations/files/{fs_object}/{tag}")
        check_error(
            response.status_code,
            info=f"({'Adding' if tag_state else 'Removing'} `{tag}` {'to' if tag_state else 'from'} {fs_object})",
        )

    def _listdir(
        self,
        user: str,
        path: str,
        properties: list[str],
        depth: int,
        exclude_self: bool,
        prop_type: PropFindType = PropFindType.DEFAULT,
    ) -> list[FsNode]:
        root = ElementTree.Element(
            "d:propfind",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
        )
        prop = ElementTree.SubElement(root, "d:prop")
        for i in properties:
            ElementTree.SubElement(prop, i)
        if prop_type in (PropFindType.VERSIONS_FILEID, PropFindType.VERSIONS_FILE_ID):
            dav_path = self._dav_get_obj_path(f"versions/{user}/versions", path, root_path="")
        elif prop_type == PropFindType.TRASHBIN:
            dav_path = self._dav_get_obj_path(f"trashbin/{user}/trash", path, root_path="")
        else:
            dav_path = self._dav_get_obj_path(user, path)
        webdav_response = self._session.dav(
            "PROPFIND",
            dav_path,
            self._element_tree_as_str(root),
            headers={"Depth": "infinity" if depth == -1 else str(depth)},
        )

        result = self._lf_parse_webdav_response(
            webdav_response,
            f"list: {user}, {path}, {properties}",
            prop_type,
        )
        if exclude_self:
            for index, v in enumerate(result):
                if v.user_path.rstrip("/") == path.strip("/"):
                    del result[index]
                    break
        return result

    def _parse_records(self, fs_records: list[dict], response_type: PropFindType) -> list[FsNode]:
        result: list[FsNode] = []
        for record in fs_records:
            obj_full_path = unquote(record.get("d:href", ""))
            obj_full_path = obj_full_path.replace(self._session.cfg.dav_url_suffix, "").lstrip("/")
            propstat = record["d:propstat"]
            fs_node = self._parse_record(obj_full_path, propstat if isinstance(propstat, list) else [propstat])
            if fs_node.etag and response_type in (
                PropFindType.VERSIONS_FILE_ID,
                PropFindType.VERSIONS_FILEID,
            ):
                fs_node.full_path = fs_node.full_path.rstrip("/")
                fs_node.info.is_version = True
                if response_type == PropFindType.VERSIONS_FILEID:
                    fs_node.info.fileid = int(fs_node.full_path.rsplit("/", 2)[-2])
                    fs_node.file_id = str(fs_node.info.fileid)
                else:
                    fs_node.file_id = fs_node.full_path.rsplit("/", 2)[-2]
            if fs_node.file_id:
                result.append(fs_node)
        return result

    @staticmethod
    def _parse_record(full_path: str, prop_stats: list[dict]) -> FsNode:
        fs_node_args = {}
        for prop_stat in prop_stats:
            if str(prop_stat.get("d:status", "")).find("200 OK") == -1:
                continue
            prop: dict = prop_stat["d:prop"]
            prop_keys = prop.keys()
            if "oc:id" in prop_keys:
                fs_node_args["file_id"] = prop["oc:id"]
            if "oc:fileid" in prop_keys:
                fs_node_args["fileid"] = int(prop["oc:fileid"])
            if "oc:size" in prop_keys:
                fs_node_args["size"] = int(prop["oc:size"])
            if "d:getcontentlength" in prop_keys:
                fs_node_args["content_length"] = int(prop["d:getcontentlength"])
            if "d:getetag" in prop_keys:
                fs_node_args["etag"] = prop["d:getetag"]
            if "d:getlastmodified" in prop_keys:
                fs_node_args["last_modified"] = prop["d:getlastmodified"]
            if "d:getcontenttype" in prop_keys:
                fs_node_args["mimetype"] = prop["d:getcontenttype"]
            if "oc:permissions" in prop_keys:
                fs_node_args["permissions"] = prop["oc:permissions"]
            if "oc:favorite" in prop_keys:
                fs_node_args["favorite"] = bool(int(prop["oc:favorite"]))
            if "nc:trashbin-filename" in prop_keys:
                fs_node_args["trashbin_filename"] = prop["nc:trashbin-filename"]
            if "nc:trashbin-original-location" in prop_keys:
                fs_node_args["trashbin_original_location"] = prop["nc:trashbin-original-location"]
            if "nc:trashbin-deletion-time" in prop_keys:
                fs_node_args["trashbin_deletion_time"] = prop["nc:trashbin-deletion-time"]
            # xz = prop.get("oc:dDC", "")
        return FsNode(full_path, **fs_node_args)

    def _lf_parse_webdav_response(
        self, webdav_res: Response, info: str, response_type: PropFindType = PropFindType.DEFAULT
    ) -> list[FsNode]:
        return self._parse_records(self._webdav_response_to_records(webdav_res, info), response_type)

    @staticmethod
    def _webdav_response_to_records(webdav_res: Response, info: str) -> list[dict]:
        check_error(webdav_res.status_code, info=info)
        if webdav_res.status_code != 207:  # multistatus
            raise NextcloudException(webdav_res.status_code, "Response is not a multistatus.", info=info)
        response_data = loads(dumps(xmltodict.parse(webdav_res.text)))
        if "d:error" in response_data:
            err = response_data["d:error"]
            raise NextcloudException(reason=f'{err["s:exception"]}: {err["s:message"]}'.replace("\n", ""), info=info)
        response = response_data["d:multistatus"].get("d:response", [])
        return [response] if isinstance(response, dict) else response

    @staticmethod
    def _dav_get_obj_path(user: str, path: str = "", root_path="/files") -> str:
        obj_dav_path = root_path
        if user:
            obj_dav_path += "/" + user
        if path:
            obj_dav_path += "/" + path.lstrip("/")
        return obj_dav_path

    @staticmethod
    def _element_tree_as_str(element) -> str:
        with BytesIO() as buffer:
            ElementTree.ElementTree(element).write(buffer, xml_declaration=True)
            buffer.seek(0)
            return buffer.read().decode("utf-8")

    @staticmethod
    def _build_search_req(xml_element_where, req: list) -> None:
        def _process_or_and(xml_element, or_and: str):
            _where_part_root = ElementTree.SubElement(xml_element, f"d:{or_and}")
            _add_value(_where_part_root)
            _add_value(_where_part_root)

        def _add_value(xml_element, val=None) -> None:
            first_val = req.pop(0) if val is None else val
            if first_val in ("or", "and"):
                _process_or_and(xml_element, first_val)
                return
            _root = ElementTree.SubElement(xml_element, f"d:{first_val}")
            _ = ElementTree.SubElement(_root, "d:prop")
            ElementTree.SubElement(_, SEARCH_PROPERTIES_MAP[req.pop(0)])
            _ = ElementTree.SubElement(_root, "d:literal")
            value = req.pop(0)
            _.text = value if isinstance(value, str) else str(value)

        while len(req):
            where_part = req.pop(0)
            if where_part in ("or", "and"):
                _process_or_and(xml_element_where, where_part)
            else:
                _add_value(xml_element_where, where_part)

    def __download2stream(self, path: str, fp, **kwargs) -> None:
        with self._session.dav_stream(
            "GET", self._dav_get_obj_path(self._session.user, path)
        ) as response:  # type: ignore
            self._session.response_headers = response.headers
            check_error(response.status_code, f"download_stream: user={self._session.user}, path={path}")
            for data_chunk in response.iter_raw(chunk_size=kwargs.get("chunk_size", 5 * 1024 * 1024)):
                fp.write(data_chunk)

    def __upload_stream(self, path: str, fp, chunk_size: int) -> FsNode:
        _dav_path = self._dav_get_obj_path(self._session.user, "nc-py-api-" + random_string(56), root_path="/uploads")
        _v2 = bool(self._session.cfg.options.upload_chunk_v2 and chunk_size >= 5 * 1024 * 1024)
        full_path = self._dav_get_obj_path(self._session.user, path)
        headers = {"Destination": self._session.cfg.dav_endpoint + full_path}
        if _v2:
            response = self._session.dav("MKCOL", _dav_path, headers=headers)
        else:
            response = self._session.dav("MKCOL", _dav_path)
        check_error(response.status_code)
        try:
            start_bytes = end_bytes = chunk_number = 0
            while True:
                piece = fp.read(chunk_size)
                if not piece:
                    break
                end_bytes = start_bytes + len(piece)
                if _v2:
                    response = self._session.dav(
                        "PUT", _dav_path + "/" + str(chunk_number), data=piece, headers=headers
                    )
                else:
                    _filename = str(start_bytes).rjust(15, "0") + "-" + str(end_bytes).rjust(15, "0")
                    response = self._session.dav("PUT", _dav_path + "/" + _filename, data=piece)
                check_error(
                    response.status_code,
                    f"upload_stream(v={_v2}): user={self._session.user}, path={path}, cur_size={end_bytes}",
                )
                start_bytes = end_bytes
                chunk_number += 1

            response = self._session.dav(
                "MOVE",
                _dav_path + "/.file",
                headers=headers,
            )
            check_error(
                response.status_code,
                f"upload_stream(v={_v2}): user={self._session.user}, path={path}, total_size={end_bytes}",
            )
            return FsNode(full_path.strip("/"), **self.__get_etag_fileid_from_response(response))
        finally:
            self._session.dav("DELETE", _dav_path)

    @staticmethod
    def __get_etag_fileid_from_response(response: Response) -> dict:
        return {"etag": response.headers.get("OC-Etag", ""), "file_id": response.headers["OC-FileId"]}
