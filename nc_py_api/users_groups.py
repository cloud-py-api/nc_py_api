"""
Nextcloud API for working with user groups.
"""

from typing import Optional, TypedDict

from ._session import NcSessionBasic
from .misc import kwargs_to_dict

ENDPOINT = "/ocs/v1.php/cloud/groups"


class GroupDetails(TypedDict):
    id: str
    display_name: str
    user_count: int
    disabled: bool
    can_add: bool
    can_remove: bool


class UserGroupsAPI:
    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_list(
        self, mask: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[str]:
        data = kwargs_to_dict(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=ENDPOINT, params=data)
        return response_data["groups"] if response_data else []

    def get_details(
        self, mask: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[GroupDetails]:
        data = kwargs_to_dict(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=f"{ENDPOINT}/details", params=data)
        return [self._to_group_details(i) for i in response_data["groups"]] if response_data else []

    def create(self, group_id: str, display_name: Optional[str] = None) -> None:
        params = {"groupid": group_id}
        if display_name is not None:
            params["displayname"] = display_name
        self._session.ocs(method="POST", path=f"{ENDPOINT}", params=params)

    def edit(self, group_id: str, display_name: str) -> None:
        params = {"key": "displayname", "value": display_name}
        self._session.ocs(method="PUT", path=f"{ENDPOINT}/{group_id}", params=params)

    def delete(self, group_id: str) -> None:
        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{group_id}")

    def get_members(self, group_id: str) -> dict:
        response_data = self._session.ocs(method="GET", path=f"{ENDPOINT}/{group_id}")
        return response_data["users"] if response_data else {}

    def get_subadmins(self, group_id: str) -> dict:
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/{group_id}/subadmins")

    @staticmethod
    def _to_group_details(reply: dict) -> GroupDetails:
        return {
            "id": reply["id"],
            "display_name": reply["displayname"],
            "user_count": reply["usercount"],
            "disabled": bool(reply["disabled"]),
            "can_add": reply["canAdd"],
            "can_remove": reply["canRemove"],
        }
