"""Nextcloud API for working with user groups."""

import dataclasses

from ._misc import kwargs_to_params
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class GroupDetails:
    """User Group information."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def group_id(self) -> str:
        """ID of the group."""
        return self._raw_data["id"]

    @property
    def display_name(self) -> str:
        """A display name of the group."""
        return self._raw_data["displayname"]

    @property
    def user_count(self) -> int:
        """Number of users in the group."""
        return self._raw_data["usercount"]

    @property
    def disabled(self) -> bool:
        """Flag indicating is group disabled."""
        return bool(self._raw_data["disabled"])

    @property
    def can_add(self) -> bool:
        """Flag indicating the caller has enough rights to add users to this group."""
        return bool(self._raw_data["canAdd"])

    @property
    def can_remove(self) -> bool:
        """Flag indicating the caller has enough rights to remove users from this group."""
        return bool(self._raw_data["canRemove"])

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.group_id}, user_count={self.user_count}, disabled={self.disabled}>"


class _UsersGroupsAPI:
    """Class providing an API for managing user groups on the Nextcloud server.

    .. note:: In NextcloudApp mode, only ``get_list`` and ``get_details`` methods are available.
    """

    _ep_base: str = "/ocs/v1.php/cloud/groups"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_list(self, mask: str | None = None, limit: int | None = None, offset: int | None = None) -> list[str]:
        """Returns a list of user groups IDs."""
        data = kwargs_to_params(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs("GET", self._ep_base, params=data)
        return response_data["groups"] if response_data else []

    def get_details(
        self, mask: str | None = None, limit: int | None = None, offset: int | None = None
    ) -> list[GroupDetails]:
        """Returns a list of user groups with detailed information."""
        data = kwargs_to_params(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs("GET", f"{self._ep_base}/details", params=data)
        return [GroupDetails(i) for i in response_data["groups"]] if response_data else []

    def create(self, group_id: str, display_name: str | None = None) -> None:
        """Creates the users group."""
        params = {"groupid": group_id}
        if display_name is not None:
            params["displayname"] = display_name
        self._session.ocs("POST", f"{self._ep_base}", params=params)

    def edit(self, group_id: str, display_name: str) -> None:
        """Edits users group information."""
        params = {"key": "displayname", "value": display_name}
        self._session.ocs("PUT", f"{self._ep_base}/{group_id}", params=params)

    def delete(self, group_id: str) -> None:
        """Removes the users group."""
        self._session.ocs("DELETE", f"{self._ep_base}/{group_id}")

    def get_members(self, group_id: str) -> list[str]:
        """Returns a list of group users."""
        response_data = self._session.ocs("GET", f"{self._ep_base}/{group_id}")
        return response_data["users"] if response_data else {}

    def get_subadmins(self, group_id: str) -> list[str]:
        """Returns list of users who is subadmins of the group."""
        return self._session.ocs("GET", f"{self._ep_base}/{group_id}/subadmins")


class _AsyncUsersGroupsAPI:
    """Class provides an async API for managing user groups on the Nextcloud server.

    .. note:: In NextcloudApp mode, only ``get_list`` and ``get_details`` methods are available.
    """

    _ep_base: str = "/ocs/v1.php/cloud/groups"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    async def get_list(self, mask: str | None = None, limit: int | None = None, offset: int | None = None) -> list[str]:
        """Returns a list of user groups IDs."""
        data = kwargs_to_params(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = await self._session.ocs("GET", self._ep_base, params=data)
        return response_data["groups"] if response_data else []

    async def get_details(
        self, mask: str | None = None, limit: int | None = None, offset: int | None = None
    ) -> list[GroupDetails]:
        """Returns a list of user groups with detailed information."""
        data = kwargs_to_params(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = await self._session.ocs("GET", f"{self._ep_base}/details", params=data)
        return [GroupDetails(i) for i in response_data["groups"]] if response_data else []

    async def create(self, group_id: str, display_name: str | None = None) -> None:
        """Creates the users group."""
        params = {"groupid": group_id}
        if display_name is not None:
            params["displayname"] = display_name
        await self._session.ocs("POST", f"{self._ep_base}", params=params)

    async def edit(self, group_id: str, display_name: str) -> None:
        """Edits users group information."""
        params = {"key": "displayname", "value": display_name}
        await self._session.ocs("PUT", f"{self._ep_base}/{group_id}", params=params)

    async def delete(self, group_id: str) -> None:
        """Removes the users group."""
        await self._session.ocs("DELETE", f"{self._ep_base}/{group_id}")

    async def get_members(self, group_id: str) -> list[str]:
        """Returns a list of group users."""
        response_data = await self._session.ocs("GET", f"{self._ep_base}/{group_id}")
        return response_data["users"] if response_data else {}

    async def get_subadmins(self, group_id: str) -> list[str]:
        """Returns list of users who is subadmins of the group."""
        return await self._session.ocs("GET", f"{self._ep_base}/{group_id}/subadmins")
