"""
Nextcloud API for working with users statuses.
"""

from typing import Literal, Optional, TypedDict, Union

from ._session import NcSessionBasic
from .exceptions import NextcloudExceptionNotFound
from .misc import check_capabilities, kwargs_to_dict, require_capabilities

ENDPOINT = "/ocs/v1.php/apps/user_status/api/v1"


class PredefinedStatus(TypedDict):
    id: str
    icon: str
    message: str
    clearAt: Optional[dict]


class UserStatus(TypedDict):
    userId: str
    message: str
    icon: Optional[str]
    clearAt: Optional[str]
    status: str


class CurrentUserStatus(UserStatus):
    messageId: Optional[str]
    messageIsPredefined: bool
    statusIsUserDefined: bool


class UserStatusAPI:
    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""

        return not check_capabilities("user_status", self._session.capabilities)

    def get_list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[UserStatus]:
        require_capabilities("user_status", self._session.capabilities)
        data = kwargs_to_dict(["limit", "offset"], limit=limit, offset=offset)
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/statuses", params=data)

    def get_current(self) -> CurrentUserStatus:
        require_capabilities("user_status", self._session.capabilities)
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/user_status")

    def get(self, user_id: str) -> Optional[UserStatus]:
        require_capabilities("user_status", self._session.capabilities)
        try:
            return self._session.ocs(method="GET", path=f"{ENDPOINT}/statuses/{user_id}")
        except NextcloudExceptionNotFound:
            return None

    def get_predefined(self) -> list[PredefinedStatus]:
        if self._session.nc_version["major"] < 27:
            return []
        require_capabilities("user_status", self._session.capabilities)
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/predefined_statuses")

    def set_predefined(self, message_id: str, clear_at: int = 0) -> None:
        if self._session.nc_version["major"] < 27:
            return
        require_capabilities("user_status", self._session.capabilities)
        params: dict[str, Union[int, str]] = {"messageId": message_id}
        if clear_at:
            params["clearAt"] = clear_at
        self._session.ocs(method="PUT", path=f"{ENDPOINT}/user_status/message/predefined", params=params)

    def set_status_type(self, value: Literal["online", "away", "dnd", "invisible", "offline"]) -> None:
        self._session.ocs(method="PUT", path=f"{ENDPOINT}/user_status/status", params={"statusType": value})

    def set(self, message: Optional[str] = None, clear_at: int = 0, status_icon: str = "") -> None:
        require_capabilities("user_status", self._session.capabilities)
        if message is None:
            self._session.ocs(method="DELETE", path=f"{ENDPOINT}/user_status/message")
            return
        if status_icon:
            require_capabilities("supports_emoji", self._session.capabilities["user_status"])
        params: dict[str, Union[int, str]] = {"message": message}
        if clear_at:
            params["clearAt"] = clear_at
        if status_icon:
            params["statusIcon"] = status_icon
        self._session.ocs(method="PUT", path=f"{ENDPOINT}/user_status/message/custom", params=params)

    def get_backup_status(self, user_id: str = "") -> Optional[UserStatus]:
        require_capabilities("user_status", self._session.capabilities)
        user_id = user_id if user_id else self._session.user
        if not user_id:
            raise ValueError("user_id can not be empty.")
        return self.get(f"_{user_id}")

    def restore_backup_status(self, message_id: str) -> Optional[CurrentUserStatus]:
        require_capabilities("user_status", self._session.capabilities)
        require_capabilities("restore", self._session.capabilities["user_status"])
        result = self._session.ocs(method="DELETE", path=f"{ENDPOINT}/user_status/revert/{message_id}")
        return result if result else None
