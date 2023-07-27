"""
Nextcloud API for working with user groups.
"""

from dataclasses import dataclass
from typing import Optional

from ._session import NcSessionBasic
from .misc import kwargs_to_dict

ENDPOINT = "/ocs/v1.php/cloud/groups"


@dataclass
class GroupDetails:
    """User Group information"""

    group_id: str
    """ID of the group"""
    display_name: str
    """Display name of the group"""
    user_count: int
    """Number of users in the group"""
    disabled: bool
    """Flag indicating is group disabled"""
    can_add: bool
    """Flag showing the caller has enough rights to add users to this group"""
    can_remove: bool
    """Flag showing the caller has enough rights to remove users from this group"""

    def __init__(self, raw_group: dict):
        self.group_id = raw_group["id"]
        self.display_name = raw_group["displayname"]
        self.user_count = raw_group["usercount"]
        self.disabled = bool(raw_group["disabled"])
        self.can_add = bool(raw_group["canAdd"])
        self.can_remove = bool(raw_group["canRemove"])


class UserGroupsAPI:
    """The class provides an API for managing user groups on the Nextcloud server.

    .. note:: In NextcloudApp mode, only ``get_list`` and ``get_details`` methods are available.
    """

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_list(
        self, mask: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[str]:
        """Returns a list of user groups IDs.

        :param mask: group ID mask to apply.
        :param limit: limits the number of results.
        :param offset: offset of results.
        """

        data = kwargs_to_dict(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=ENDPOINT, params=data)
        return response_data["groups"] if response_data else []

    def get_details(
        self, mask: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[GroupDetails]:
        """Returns a list of user groups with detailed information.

        :param mask: group ID mask to apply.
        :param limit: limits the number of results.
        :param offset: offset of results.
        """

        data = kwargs_to_dict(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=f"{ENDPOINT}/details", params=data)
        return [GroupDetails(i) for i in response_data["groups"]] if response_data else []

    def create(self, group_id: str, display_name: Optional[str] = None) -> None:
        """Creates the users group.

        :param group_id: the ID of group to be created.
        :param display_name: display name for a created group.
        """

        params = {"groupid": group_id}
        if display_name is not None:
            params["displayname"] = display_name
        self._session.ocs(method="POST", path=f"{ENDPOINT}", params=params)

    def edit(self, group_id: str, display_name: str) -> None:
        """Edits users group information.

        :param group_id: the ID of group to edit info.
        :param display_name: new group display name.
        """

        params = {"key": "displayname", "value": display_name}
        self._session.ocs(method="PUT", path=f"{ENDPOINT}/{group_id}", params=params)

    def delete(self, group_id: str) -> None:
        """Removes the users group.

        :param group_id: the ID of group to remove.
        """

        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{group_id}")

    def get_members(self, group_id: str) -> list[str]:
        """Returns a list of group users.

        :param group_id: Group ID to get the list of members.
        """

        response_data = self._session.ocs(method="GET", path=f"{ENDPOINT}/{group_id}")
        return response_data["users"] if response_data else {}

    def get_subadmins(self, group_id: str) -> list[str]:
        """Returns list of users who is subadmins of the group.

        :param group_id: group ID to get the list of subadmins.
        """

        return self._session.ocs(method="GET", path=f"{ENDPOINT}/{group_id}/subadmins")
