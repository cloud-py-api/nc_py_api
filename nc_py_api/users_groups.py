"""Nextcloud API for working with user groups."""

import dataclasses
import typing

from ._misc import kwargs_to_params
from ._session import NcSessionBasic


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

    def get_list(
        self, mask: typing.Optional[str] = None, limit: typing.Optional[int] = None, offset: typing.Optional[int] = None
    ) -> list[str]:
        """Returns a list of user groups IDs.

        :param mask: group ID mask to apply.
        :param limit: limits the number of results.
        :param offset: offset of results.
        """
        data = kwargs_to_params(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=self._ep_base, params=data)
        return response_data["groups"] if response_data else []

    def get_details(
        self, mask: typing.Optional[str] = None, limit: typing.Optional[int] = None, offset: typing.Optional[int] = None
    ) -> list[GroupDetails]:
        """Returns a list of user groups with detailed information.

        :param mask: group ID mask to apply.
        :param limit: limits the number of results.
        :param offset: offset of results.
        """
        data = kwargs_to_params(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=f"{self._ep_base}/details", params=data)
        return [GroupDetails(i) for i in response_data["groups"]] if response_data else []

    def create(self, group_id: str, display_name: typing.Optional[str] = None) -> None:
        """Creates the users group.

        :param group_id: the ID of group to be created.
        :param display_name: display name for a created group.
        """
        params = {"groupid": group_id}
        if display_name is not None:
            params["displayname"] = display_name
        self._session.ocs(method="POST", path=f"{self._ep_base}", params=params)

    def edit(self, group_id: str, display_name: str) -> None:
        """Edits users group information.

        :param group_id: the ID of group to edit info.
        :param display_name: new group display name.
        """
        params = {"key": "displayname", "value": display_name}
        self._session.ocs(method="PUT", path=f"{self._ep_base}/{group_id}", params=params)

    def delete(self, group_id: str) -> None:
        """Removes the users group.

        :param group_id: the ID of group to remove.
        """
        self._session.ocs(method="DELETE", path=f"{self._ep_base}/{group_id}")

    def get_members(self, group_id: str) -> list[str]:
        """Returns a list of group users.

        :param group_id: Group ID to get the list of members.
        """
        response_data = self._session.ocs(method="GET", path=f"{self._ep_base}/{group_id}")
        return response_data["users"] if response_data else {}

    def get_subadmins(self, group_id: str) -> list[str]:
        """Returns list of users who is subadmins of the group.

        :param group_id: group ID to get the list of subadmins.
        """
        return self._session.ocs(method="GET", path=f"{self._ep_base}/{group_id}/subadmins")
