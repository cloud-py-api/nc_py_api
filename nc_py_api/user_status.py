"""Nextcloud API for working with user statuses."""

import dataclasses
import typing

from ._exceptions import NextcloudExceptionNotFound
from ._misc import check_capabilities, kwargs_to_params, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class ClearAt:
    """Determination when a user's predefined status will be cleared."""

    clear_type: str
    """Possible values: ``period``, ``end-of``"""
    time: str | int
    """Depending of ``type`` it can be number of seconds relative to ``now`` or one of the next values: ``day``"""

    def __init__(self, raw_data: dict):
        self.clear_type = raw_data["type"]
        self.time = raw_data["time"]


@dataclasses.dataclass
class PredefinedStatus:
    """Definition of the predefined status."""

    status_id: str
    """ID of the predefined status"""
    icon: str
    """Icon in string(UTF) format"""
    message: str
    """The message defined for this status. It is translated, so it depends on the user's language setting."""
    clear_at: ClearAt | None
    """When the default, if not override, the predefined status will be cleared."""

    def __init__(self, raw_status: dict):
        self.status_id = raw_status["id"]
        self.icon = raw_status["icon"]
        self.message = raw_status["message"]
        clear_at_raw = raw_status.get("clearAt")
        if clear_at_raw:
            self.clear_at = ClearAt(clear_at_raw)
        else:
            self.clear_at = None


@dataclasses.dataclass
class UserStatus:
    """Information about user status."""

    user_id: str
    """The ID of the user this status is for"""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data
        self.user_id = raw_data["userId"]

    @property
    def status_message(self) -> str:
        """Message of the status."""
        return self._raw_data.get("message", "")

    @property
    def status_icon(self) -> str:
        """The icon picked by the user (must be one emoji)."""
        return self._raw_data.get("icon", "")

    @property
    def status_clear_at(self) -> int | None:
        """Unix Timestamp representing the time to clear the status."""
        return self._raw_data.get("clearAt", None)

    @property
    def status_type(self) -> str:
        """Status type, on of the: online, away, dnd, invisible, offline."""
        return self._raw_data.get("status", "")

    def __repr__(self):
        return f"<{self.__class__.__name__} user_id={self.user_id}, status_type={self.status_type}>"


@dataclasses.dataclass(init=False)
class CurrentUserStatus(UserStatus):
    """Information about current user status."""

    @property
    def status_id(self) -> str | None:
        """ID of the predefined status."""
        return self._raw_data["messageId"]

    @property
    def message_predefined(self) -> bool:
        """*True* if the status is predefined, *False* otherwise."""
        return self._raw_data["messageIsPredefined"]

    @property
    def status_type_defined(self) -> bool:
        """*True* if :py:attr:`UserStatus.status_type` is set by user, *False* otherwise."""
        return self._raw_data["statusIsUserDefined"]

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} user_id={self.user_id}, status_type={self.status_type},"
            f" status_id={self.status_id}>"
        )


class _UserStatusAPI:
    """Class providing the user status management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/user_status/api/v1"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("user_status.enabled", self._session.capabilities)

    def get_list(self, limit: int | None = None, offset: int | None = None) -> list[UserStatus]:
        """Returns statuses for all users."""
        require_capabilities("user_status.enabled", self._session.capabilities)
        data = kwargs_to_params(["limit", "offset"], limit=limit, offset=offset)
        result = self._session.ocs("GET", f"{self._ep_base}/statuses", params=data)
        return [UserStatus(i) for i in result]

    def get_current(self) -> CurrentUserStatus:
        """Returns the current user status."""
        require_capabilities("user_status.enabled", self._session.capabilities)
        return CurrentUserStatus(self._session.ocs("GET", f"{self._ep_base}/user_status"))

    def get(self, user_id: str) -> UserStatus | None:
        """Returns the user status for the specified user."""
        require_capabilities("user_status.enabled", self._session.capabilities)
        try:
            return UserStatus(self._session.ocs("GET", f"{self._ep_base}/statuses/{user_id}"))
        except NextcloudExceptionNotFound:
            return None

    def get_predefined(self) -> list[PredefinedStatus]:
        """Returns a list of predefined statuses available for installation on this Nextcloud instance."""
        if self._session.nc_version["major"] < 27:
            return []
        require_capabilities("user_status.enabled", self._session.capabilities)
        result = self._session.ocs("GET", f"{self._ep_base}/predefined_statuses")
        return [PredefinedStatus(i) for i in result]

    def set_predefined(self, status_id: str, clear_at: int = 0) -> None:
        """Set predefined status for the current user.

        :param status_id: ``predefined`` status ID.
        :param clear_at: *optional* time in seconds before the status is cleared.
        """
        if self._session.nc_version["major"] < 27:
            return
        require_capabilities("user_status.enabled", self._session.capabilities)
        params: dict[str, int | str] = {"messageId": status_id}
        if clear_at:
            params["clearAt"] = clear_at
        self._session.ocs("PUT", f"{self._ep_base}/user_status/message/predefined", params=params)

    def set_status_type(self, value: typing.Literal["online", "away", "dnd", "invisible", "offline"]) -> None:
        """Sets the status type for the current user."""
        require_capabilities("user_status.enabled", self._session.capabilities)
        self._session.ocs("PUT", f"{self._ep_base}/user_status/status", params={"statusType": value})

    def set_status(self, message: str | None = None, clear_at: int = 0, status_icon: str = "") -> None:
        """Sets current user status.

        :param message: Message text to set in the status.
        :param clear_at: Unix Timestamp, representing the time to clear the status.
        :param status_icon: The icon picked by the user (must be one emoji)
        """
        require_capabilities("user_status.enabled", self._session.capabilities)
        if message is None:
            self._session.ocs("DELETE", f"{self._ep_base}/user_status/message")
            return
        if status_icon:
            require_capabilities("user_status.supports_emoji", self._session.capabilities)
        params: dict[str, int | str] = {"message": message}
        if clear_at:
            params["clearAt"] = clear_at
        if status_icon:
            params["statusIcon"] = status_icon
        self._session.ocs("PUT", f"{self._ep_base}/user_status/message/custom", params=params)

    def get_backup_status(self, user_id: str = "") -> UserStatus | None:
        """Get the backup status of the user if any."""
        require_capabilities("user_status.enabled", self._session.capabilities)
        user_id = user_id if user_id else self._session.user
        if not user_id:
            raise ValueError("user_id can not be empty.")
        return self.get(f"_{user_id}")

    def restore_backup_status(self, status_id: str) -> CurrentUserStatus | None:
        """Restores the backup state as current for the current user."""
        require_capabilities("user_status.enabled", self._session.capabilities)
        require_capabilities("user_status.restore", self._session.capabilities)
        result = self._session.ocs("DELETE", f"{self._ep_base}/user_status/revert/{status_id}")
        return result if result else None


class _AsyncUserStatusAPI:
    """Class provides async user status management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/user_status/api/v1"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("user_status.enabled", await self._session.capabilities)

    async def get_list(self, limit: int | None = None, offset: int | None = None) -> list[UserStatus]:
        """Returns statuses for all users."""
        require_capabilities("user_status.enabled", await self._session.capabilities)
        data = kwargs_to_params(["limit", "offset"], limit=limit, offset=offset)
        result = await self._session.ocs("GET", f"{self._ep_base}/statuses", params=data)
        return [UserStatus(i) for i in result]

    async def get_current(self) -> CurrentUserStatus:
        """Returns the current user status."""
        require_capabilities("user_status.enabled", await self._session.capabilities)
        return CurrentUserStatus(await self._session.ocs("GET", f"{self._ep_base}/user_status"))

    async def get(self, user_id: str) -> UserStatus | None:
        """Returns the user status for the specified user."""
        require_capabilities("user_status.enabled", await self._session.capabilities)
        try:
            return UserStatus(await self._session.ocs("GET", f"{self._ep_base}/statuses/{user_id}"))
        except NextcloudExceptionNotFound:
            return None

    async def get_predefined(self) -> list[PredefinedStatus]:
        """Returns a list of predefined statuses available for installation on this Nextcloud instance."""
        if (await self._session.nc_version)["major"] < 27:
            return []
        require_capabilities("user_status.enabled", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/predefined_statuses")
        return [PredefinedStatus(i) for i in result]

    async def set_predefined(self, status_id: str, clear_at: int = 0) -> None:
        """Set predefined status for the current user.

        :param status_id: ``predefined`` status ID.
        :param clear_at: *optional* time in seconds before the status is cleared.
        """
        if (await self._session.nc_version)["major"] < 27:
            return
        require_capabilities("user_status.enabled", await self._session.capabilities)
        params: dict[str, int | str] = {"messageId": status_id}
        if clear_at:
            params["clearAt"] = clear_at
        await self._session.ocs("PUT", f"{self._ep_base}/user_status/message/predefined", params=params)

    async def set_status_type(self, value: typing.Literal["online", "away", "dnd", "invisible", "offline"]) -> None:
        """Sets the status type for the current user."""
        require_capabilities("user_status.enabled", await self._session.capabilities)
        await self._session.ocs("PUT", f"{self._ep_base}/user_status/status", params={"statusType": value})

    async def set_status(self, message: str | None = None, clear_at: int = 0, status_icon: str = "") -> None:
        """Sets current user status.

        :param message: Message text to set in the status.
        :param clear_at: Unix Timestamp, representing the time to clear the status.
        :param status_icon: The icon picked by the user (must be one emoji)
        """
        require_capabilities("user_status.enabled", await self._session.capabilities)
        if message is None:
            await self._session.ocs("DELETE", f"{self._ep_base}/user_status/message")
            return
        if status_icon:
            require_capabilities("user_status.supports_emoji", await self._session.capabilities)
        params: dict[str, int | str] = {"message": message}
        if clear_at:
            params["clearAt"] = clear_at
        if status_icon:
            params["statusIcon"] = status_icon
        await self._session.ocs("PUT", f"{self._ep_base}/user_status/message/custom", params=params)

    async def get_backup_status(self, user_id: str = "") -> UserStatus | None:
        """Get the backup status of the user if any."""
        require_capabilities("user_status.enabled", await self._session.capabilities)
        user_id = user_id if user_id else await self._session.user
        if not user_id:
            raise ValueError("user_id can not be empty.")
        return await self.get(f"_{user_id}")

    async def restore_backup_status(self, status_id: str) -> CurrentUserStatus | None:
        """Restores the backup state as current for the current user."""
        require_capabilities("user_status.enabled", await self._session.capabilities)
        require_capabilities("user_status.restore", await self._session.capabilities)
        result = await self._session.ocs("DELETE", f"{self._ep_base}/user_status/revert/{status_id}")
        return result if result else None
