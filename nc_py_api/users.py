"""
Nextcloud API for working with users.
"""

from typing import Optional

from ._session import NcSessionBasic
from .misc import kwargs_to_dict

ENDPOINT_BASE = "/ocs/v1.php/cloud"
ENDPOINT = f"{ENDPOINT_BASE}/users"


class UserAPI:
    def __init__(self, session: NcSessionBasic):
        self._session = session

    def list(self, mask: Optional[str] = "", limit: Optional[int] = None, offset: Optional[int] = None) -> dict:
        data = kwargs_to_dict(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=ENDPOINT, params=data)
        return response_data["users"] if response_data else {}

    def get(self, user_id: str = "") -> dict:
        if not user_id:
            user_id = self._session.user
        if not user_id:
            raise ValueError("user_id can not be empty.")
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/{user_id}")

    def create(self, user_id: str, **kwargs) -> dict:
        password = kwargs.get("password", None)
        email = kwargs.get("email", None)
        if password is None and email is None:
            raise ValueError("Either password or email must be set")
        data = {"userid": user_id}
        for k in ("password", "displayname", "email", "groups", "subadmin", "quota", "language"):
            if k in kwargs:
                data[k] = kwargs[k]
        return self._session.ocs(method="POST", path=ENDPOINT, params=data)

    def delete(self, user_id: str) -> dict:
        return self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{user_id}")

    def enable(self, user_id: str) -> dict:
        return self._session.ocs(method="PUT", path=f"{ENDPOINT}/{user_id}/enable")

    def disable(self, user_id: str) -> dict:
        return self._session.ocs(method="PUT", path=f"{ENDPOINT}/{user_id}/disable")

    def resend_welcome_email(self) -> dict:
        return self._session.ocs(method="POST", path=f"{ENDPOINT}/user/welcome")

    def editable_fields(self) -> dict:
        return self._session.ocs(method="GET", path=f"{ENDPOINT_BASE}/user/fields")

    def edit(self, user_id: str, **kwargs) -> dict:
        return self._session.ocs(method="PUT", path=f"{ENDPOINT}/{user_id}", params={**kwargs})

    def add_to_group(self, user_id: str, group_id: str) -> dict:
        return self._session.ocs(method="POST", path=f"{ENDPOINT}/{user_id}/groups", params={"groupid": group_id})

    def remove_from_group(self, user_id: str, group_id: str) -> dict:
        return self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{user_id}/groups", params={"groupid": group_id})

    def promote_to_subadmin(self, user_id: str, group_id: str) -> dict:
        return self._session.ocs(method="POST", path=f"{ENDPOINT}/{user_id}/subadmins", params={"groupid": group_id})

    def demote_from_subadmin(self, user_id: str, group_id: str) -> dict:
        return self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{user_id}/subadmins", params={"groupid": group_id})
