"""Nextcloud API for working with System Tags."""

from ._exceptions import NextcloudExceptionNotFound, check_error
from ._misc import check_capabilities, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic
from .files import SystemTag
from .files._files import build_list_tag_req, build_list_tags_response, build_update_tag_req, element_tree_as_str


class _SystemTagsAPI:
    """Class providing the System Tags API on the Nextcloud server."""

    _ep_base: str = "/systemtags"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports System Tags, False otherwise."""
        return not check_capabilities("files", self._session.capabilities)

    def get_list(self) -> list[SystemTag]:
        """Returns a list of all system tags."""
        require_capabilities("files", self._session.capabilities)
        root = build_list_tag_req()
        response = self._session.adapter_dav.request("PROPFIND", self._ep_base, data=element_tree_as_str(root))
        return build_list_tags_response(response)

    def create(self, name: str, user_visible: bool = True, user_assignable: bool = True) -> SystemTag:
        """Creates a new system tag.

        :param name: Name of the tag.
        :param user_visible: Should the tag be visible in the UI.
        :param user_assignable: Can the tag be assigned from the UI.
        :returns: SystemTag object representing the created tag.
        """
        require_capabilities("files", self._session.capabilities)
        if not name:
            raise ValueError("`name` parameter cannot be empty")
        response = self._session.adapter_dav.post(
            self._ep_base,
            json={
                "name": name,
                "userVisible": user_visible,
                "userAssignable": user_assignable,
            },
        )
        check_error(response, info=f"create({name})")
        # After creation, we need to fetch the tag to return it
        # The response should contain the tag ID, but we'll fetch it by name for now
        tags = self.get_list()
        matching = [tag for tag in tags if tag.display_name == name]
        if matching:
            return matching[-1]  # Return the most recently created one
        raise NextcloudExceptionNotFound(f"Tag '{name}' was created but could not be retrieved.")

    def update(
        self,
        tag_id: int | SystemTag,
        name: str | None = None,
        user_visible: bool | None = None,
        user_assignable: bool | None = None,
    ) -> None:
        """Updates a system tag.

        :param tag_id: ID of the tag or SystemTag object to update.
        :param name: New name for the tag.
        :param user_visible: New visibility setting for the tag.
        :param user_assignable: New assignability setting for the tag.
        """
        require_capabilities("files", self._session.capabilities)
        tag_id = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        root = build_update_tag_req(name, user_visible, user_assignable)
        response = self._session.adapter_dav.request(
            "PROPPATCH", f"{self._ep_base}/{tag_id}", data=element_tree_as_str(root)
        )
        check_error(response)

    def delete(self, tag_id: int | SystemTag) -> None:
        """Deletes a system tag.

        :param tag_id: ID of the tag or SystemTag object to delete.
        """
        require_capabilities("files", self._session.capabilities)
        tag_id = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        response = self._session.adapter_dav.delete(f"{self._ep_base}/{tag_id}")
        check_error(response)

    def get_by_name(self, tag_name: str) -> SystemTag:
        """Returns a system tag by its name.

        :param tag_name: Name of the tag to find.
        :returns: SystemTag object.
        :raises NextcloudExceptionNotFound: If tag with the given name is not found.
        """
        require_capabilities("files", self._session.capabilities)
        tags = self.get_list()
        matching = [tag for tag in tags if tag.display_name == tag_name]
        if not matching:
            raise NextcloudExceptionNotFound(f"Tag with name='{tag_name}' not found.")
        return matching[0]


class _AsyncSystemTagsAPI:
    """Class provides async System Tags API on the Nextcloud server."""

    _ep_base: str = "/systemtags"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports System Tags, False otherwise."""
        return not check_capabilities("files", await self._session.capabilities)

    async def get_list(self) -> list[SystemTag]:
        """Returns a list of all system tags."""
        require_capabilities("files", await self._session.capabilities)
        root = build_list_tag_req()
        response = await self._session.adapter_dav.request("PROPFIND", self._ep_base, data=element_tree_as_str(root))
        return build_list_tags_response(response)

    async def create(self, name: str, user_visible: bool = True, user_assignable: bool = True) -> SystemTag:
        """Creates a new system tag.

        :param name: Name of the tag.
        :param user_visible: Should the tag be visible in the UI.
        :param user_assignable: Can the tag be assigned from the UI.
        :returns: SystemTag object representing the created tag.
        """
        require_capabilities("files", await self._session.capabilities)
        if not name:
            raise ValueError("`name` parameter cannot be empty")
        response = await self._session.adapter_dav.post(
            self._ep_base,
            json={
                "name": name,
                "userVisible": user_visible,
                "userAssignable": user_assignable,
            },
        )
        check_error(response, info=f"create({name})")
        # After creation, we need to fetch the tag to return it
        tags = await self.get_list()
        matching = [tag for tag in tags if tag.display_name == name]
        if matching:
            return matching[-1]  # Return the most recently created one
        raise NextcloudExceptionNotFound(f"Tag '{name}' was created but could not be retrieved.")

    async def update(
        self,
        tag_id: int | SystemTag,
        name: str | None = None,
        user_visible: bool | None = None,
        user_assignable: bool | None = None,
    ) -> None:
        """Updates a system tag.

        :param tag_id: ID of the tag or SystemTag object to update.
        :param name: New name for the tag.
        :param user_visible: New visibility setting for the tag.
        :param user_assignable: New assignability setting for the tag.
        """
        require_capabilities("files", await self._session.capabilities)
        tag_id = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        root = build_update_tag_req(name, user_visible, user_assignable)
        response = await self._session.adapter_dav.request(
            "PROPPATCH", f"{self._ep_base}/{tag_id}", data=element_tree_as_str(root)
        )
        check_error(response)

    async def delete(self, tag_id: int | SystemTag) -> None:
        """Deletes a system tag.

        :param tag_id: ID of the tag or SystemTag object to delete.
        """
        require_capabilities("files", await self._session.capabilities)
        tag_id = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        response = await self._session.adapter_dav.delete(f"{self._ep_base}/{tag_id}")
        check_error(response)

    async def get_by_name(self, tag_name: str) -> SystemTag:
        """Returns a system tag by its name.

        :param tag_name: Name of the tag to find.
        :returns: SystemTag object.
        :raises NextcloudExceptionNotFound: If tag with the given name is not found.
        """
        require_capabilities("files", await self._session.capabilities)
        tags = await self.get_list()
        matching = [tag for tag in tags if tag.display_name == tag_name]
        if not matching:
            raise NextcloudExceptionNotFound(f"Tag with name='{tag_name}' not found.")
        return matching[0]
