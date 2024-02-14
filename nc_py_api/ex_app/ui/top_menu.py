"""Nextcloud API for working with Top App menu."""

import dataclasses

from ..._exceptions import NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import AsyncNcSessionApp, NcSessionApp


@dataclasses.dataclass
class UiTopMenuEntry:
    """App top menu entry description."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def appid(self) -> str:
        """App ID for which this entry is."""
        return self._raw_data["appid"]

    @property
    def name(self) -> str:
        """Top Menu entry name, acts like ID."""
        return self._raw_data["name"]

    @property
    def display_name(self) -> str:
        """Display name of the entry."""
        return self._raw_data["display_name"]

    @property
    def icon(self) -> str:
        """Relative to the ExApp url with icon or empty value to use the default one icon."""
        return self._raw_data["icon"] if self._raw_data["icon"] else ""

    @property
    def admin_required(self) -> bool:
        """Flag that determines whether the entry menu is displayed only for administrators."""
        return bool(int(self._raw_data["admin_required"]))

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, admin_required={self.admin_required}>"


class _UiTopMenuAPI:
    """API for the top menu app nav bar in Nextcloud, avalaible as **nc.ui.top_menu.<method>**."""

    _ep_suffix: str = "ui/top-menu"

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(self, name: str, display_name: str, icon: str = "", admin_required=False) -> None:
        """Registers or edit the App entry in Top Meny.

        :param name: Unique name for the menu entry.
        :param display_name: Display name of the menu entry.
        :param icon: Optional, url relative to the ExApp, like: "img/icon.svg"
        :param admin_required: Boolean value indicating should be Entry visible to all or only to admins.
        """
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "icon": icon,
            "adminRequired": int(admin_required),
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes App entry in Top Menu."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{self._ep_suffix}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_entry(self, name: str) -> UiTopMenuEntry | None:
        """Get information of the top meny entry for current app."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return UiTopMenuEntry(
                self._session.ocs("GET", f"{self._session.ae_url}/{self._ep_suffix}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None


class _AsyncUiTopMenuAPI:
    """Async API for the top menu app nav bar in Nextcloud."""

    _ep_suffix: str = "ui/top-menu"

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register(self, name: str, display_name: str, icon: str = "", admin_required=False) -> None:
        """Registers or edit the App entry in Top Meny.

        :param name: Unique name for the menu entry.
        :param display_name: Display name of the menu entry.
        :param icon: Optional, url relative to the ExApp, like: "img/icon.svg"
        :param admin_required: Boolean value indicating should be Entry visible to all or only to admins.
        """
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "icon": icon,
            "adminRequired": int(admin_required),
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix}", json=params)

    async def unregister(self, name: str, not_fail=True) -> None:
        """Removes App entry in Top Menu."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{self._ep_suffix}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_entry(self, name: str) -> UiTopMenuEntry | None:
        """Get information of the top meny entry for current app."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return UiTopMenuEntry(
                await self._session.ocs("GET", f"{self._session.ae_url}/{self._ep_suffix}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None
