"""
Nextcloud API for working with user groups.
"""

from typing import Optional

from ._session import NcSessionBasic
from .misc import kwargs_to_dict

ENDPOINT = "/ocs/v1.php/cloud/groups"


class UsersGroupsAPI:
    def __init__(self, session: NcSessionBasic):
        self._session = session

    def list(self, mask: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> dict:
        data = kwargs_to_dict(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=ENDPOINT, params=data)
        return response_data["groups"] if response_data else {}

    def create(self, group_id: str) -> dict:
        return self._session.ocs(method="POST", path=f"{ENDPOINT}", params={"groupid": group_id})

    def edit(self, group_id: str, **kwargs) -> dict:
        return self._session.ocs(method="PUT", path=f"{ENDPOINT}/{group_id}", params={**kwargs})

    def delete(self, group_id: str) -> dict:
        return self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{group_id}")

    def get_members(self, group_id: str) -> dict:
        response_data = self._session.ocs(method="GET", path=f"{ENDPOINT}/{group_id}")
        return response_data["users"] if response_data else {}

    def get_subadmins(self, group_id: str) -> dict:
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/{group_id}/subadmins")
