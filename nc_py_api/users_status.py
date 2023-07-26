"""
Nextcloud API for working with user statuses.
"""

from dataclasses import dataclass
from typing import Literal, Optional, Union

from ._session import NcSessionBasic
from .exceptions import NextcloudExceptionNotFound
from .misc import check_capabilities, kwargs_to_dict, require_capabilities

ENDPOINT = "/ocs/v1.php/apps/user_status/api/v1"


@dataclass
class ClearAt:
    """Determination when a user's predefined status will be cleared."""

    type: str
    """Possible values: ``period``, ``end-of``"""
    time: Union[str, int]
    """Depending of ``type`` it can be number of seconds relative to ``now`` or one of the next values: ``day``"""

    def __init__(self, raw_data: dict):
        self.type = raw_data["type"]
        self.time = raw_data["time"]


@dataclass
class PredefinedStatus:
    """Definition of the predefined status."""

    status_id: str
    """ID of the predefined status"""
    icon: str
    """Icon in string(UTF) format"""
    message: str
    """The message defined for this status. It is translated, so it depends on the user's language setting."""
    clear_at: Optional[ClearAt]
    """When the default, if not override, the predefined status will be cleared."""

    def __init__(self, raw_status: dict):
        self.status_id = raw_status["id"]
        self.icon = raw_status["icon"]
        self.message = raw_status["message"]
        clear_at_raw = raw_status.get("clearAt", None)
        if clear_at_raw:
            self.clear_at = ClearAt(clear_at_raw)
        else:
            self.clear_at = None


@dataclass
class UserStatus:
    """Information about user status."""

    user_id: str
    """The ID of the user this status is for"""
    message: str
    """Message of the status"""
    icon: Optional[str]
    """The icon picked by the user (must be one emoji)"""
    clear_at: Optional[int]
    """Unix Timestamp representing the time to clear the status."""
    status_type: str
    """Status type, on of the: online, away, dnd, invisible, offline"""

    def __init__(self, raw_status: dict):
        self.user_id = raw_status["userId"]
        self.message = raw_status["message"]
        self.icon = raw_status["icon"]
        self.clear_at = raw_status["clearAt"]
        self.status_type = raw_status["status"]


@dataclass
class CurrentUserStatus(UserStatus):
    """Information about current user status."""

    status_id: Optional[str]
    """ID of the predefined status"""
    predefined: bool
    """*True* if status if predefined, *False* otherwise"""
    status_type_defined: bool
    """*True* if :py:attr:`UserStatus.status_type` is set by user, *False* otherwise"""

    def __init__(self, raw_status: dict):
        super().__init__(raw_status)
        self.status_id = raw_status["messageId"]
        self.predefined = raw_status["messageIsPredefined"]
        self.status_type_defined = raw_status["statusIsUserDefined"]


class UserStatusAPI:
    """The class provides the user status management API on the Nextcloud server."""

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""

        return not check_capabilities("user_status", self._session.capabilities)

    def get_list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[UserStatus]:
        """Returns statuses for all users.

        :param limit: limits the number of results.
        :param offset: offset of results.
        """

        require_capabilities("user_status", self._session.capabilities)
        data = kwargs_to_dict(["limit", "offset"], limit=limit, offset=offset)
        result = self._session.ocs(method="GET", path=f"{ENDPOINT}/statuses", params=data)
        return [UserStatus(i) for i in result]

    def get_current(self) -> CurrentUserStatus:
        """Returns the current user status."""

        require_capabilities("user_status", self._session.capabilities)
        return CurrentUserStatus(self._session.ocs(method="GET", path=f"{ENDPOINT}/user_status"))

    def get(self, user_id: str) -> Optional[UserStatus]:
        """Returns the user status for the specified user.

        :param user_id: User ID for getting status.
        """

        require_capabilities("user_status", self._session.capabilities)
        try:
            return UserStatus(self._session.ocs(method="GET", path=f"{ENDPOINT}/statuses/{user_id}"))
        except NextcloudExceptionNotFound:
            return None

    def get_predefined(self) -> list[PredefinedStatus]:
        """Returns a list of predefined statuses available for installation on this Nextcloud instance."""

        if self._session.nc_version["major"] < 27:
            return []
        require_capabilities("user_status", self._session.capabilities)
        result = self._session.ocs(method="GET", path=f"{ENDPOINT}/predefined_statuses")
        return [PredefinedStatus(i) for i in result]

    def set_predefined(self, status_id: str, clear_at: int = 0) -> None:
        """Set predefined status for the current user.

        :param status_id: ``predefined`` status ID.
        :param clear_at: *optional* time in seconds before the status is cleared.
        """

        if self._session.nc_version["major"] < 27:
            return
        require_capabilities("user_status", self._session.capabilities)
        params: dict[str, Union[int, str]] = {"messageId": status_id}
        if clear_at:
            params["clearAt"] = clear_at
        self._session.ocs(method="PUT", path=f"{ENDPOINT}/user_status/message/predefined", params=params)

    def set_status_type(self, value: Literal["online", "away", "dnd", "invisible", "offline"]) -> None:
        """Sets the status type for the current user."""

        self._session.ocs(method="PUT", path=f"{ENDPOINT}/user_status/status", params={"statusType": value})

    def set(self, message: Optional[str] = None, clear_at: int = 0, status_icon: str = "") -> None:
        """Sets current user status.

        :param message: Message text to set in the status.
        :param clear_at: Unix Timestamp, representing the time to clear the status.
        :param status_icon: The icon picked by the user (must be one emoji)
        """

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
        """Get the backup status of the user if any.

        :param user_id: User ID for getting status.
        """

        require_capabilities("user_status", self._session.capabilities)
        user_id = user_id if user_id else self._session.user
        if not user_id:
            raise ValueError("user_id can not be empty.")
        return self.get(f"_{user_id}")

    def restore_backup_status(self, status_id: str) -> Optional[CurrentUserStatus]:
        """Restores the backup state as current for the current user.

        :param status_id: backup status ID.
        """

        require_capabilities("user_status", self._session.capabilities)
        require_capabilities("restore", self._session.capabilities["user_status"])
        result = self._session.ocs(method="DELETE", path=f"{ENDPOINT}/user_status/revert/{status_id}")
        return result if result else None
