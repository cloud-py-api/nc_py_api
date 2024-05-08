"""Nextcloud API for working with drop-down file's menu."""

import dataclasses
import warnings

from ..._exceptions import NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import AsyncNcSessionApp, NcSessionApp


@dataclasses.dataclass
class UiFileActionEntry:
    """Files app, right click file action entry description."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def appid(self) -> str:
        """App ID for which this entry is."""
        return self._raw_data["appid"]

    @property
    def name(self) -> str:
        """File action name, acts like ID."""
        return self._raw_data["name"]

    @property
    def display_name(self) -> str:
        """Display name of the entry."""
        return self._raw_data["display_name"]

    @property
    def mime(self) -> str:
        """For which file types this entry applies."""
        return self._raw_data["mime"]

    @property
    def permissions(self) -> int:
        """For which file permissions this entry applies."""
        return int(self._raw_data["permissions"])

    @property
    def order(self) -> int:
        """Order of the entry in the file action list."""
        return int(self._raw_data["order"])

    @property
    def icon(self) -> str:
        """Relative to the ExApp url with icon or empty value to use the default one icon."""
        return self._raw_data["icon"] if self._raw_data["icon"] else ""

    @property
    def action_handler(self) -> str:
        """Relative ExApp url which will be called if user click on the entry."""
        return self._raw_data["action_handler"]

    @property
    def version(self) -> str:
        """AppAPI `2.6.0` supports new version of UiActions(https://github.com/cloud-py-api/app_api/pull/284)."""
        return self._raw_data.get("version", "1.0")

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, mime={self.mime}, handler={self.action_handler}>"


class _UiFilesActionsAPI:
    """API for the drop-down menu in Nextcloud **Files app**, avalaible as **nc.ui.files_dropdown_menu.<method>**."""

    _ep_suffix: str = "ui/files-actions-menu"

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(self, name: str, display_name: str, callback_url: str, **kwargs) -> None:
        """Registers the files dropdown menu element."""
        warnings.warn(
            "register() is deprecated and will be removed in a future version. Use register_ex() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "actionHandler": callback_url,
            "icon": kwargs.get("icon", ""),
            "mime": kwargs.get("mime", "file"),
            "permissions": kwargs.get("permissions", 31),
            "order": kwargs.get("order", 0),
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix}", json=params)

    def register_ex(self, name: str, display_name: str, callback_url: str, **kwargs) -> None:
        """Registers the files dropdown menu element(extended version that receives ``ActionFileInfoEx``)."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "actionHandler": callback_url,
            "icon": kwargs.get("icon", ""),
            "mime": kwargs.get("mime", "file"),
            "permissions": kwargs.get("permissions", 31),
            "order": kwargs.get("order", 0),
        }
        self._session.ocs("POST", f"{self._session.ae_url_v2}/{self._ep_suffix}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes files dropdown menu element."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{self._ep_suffix}", json={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_entry(self, name: str) -> UiFileActionEntry | None:
        """Get information of the file action meny entry."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return UiFileActionEntry(
                self._session.ocs("GET", f"{self._session.ae_url}/{self._ep_suffix}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None


class _AsyncUiFilesActionsAPI:
    """Async API for the drop-down menu in Nextcloud **Files app**."""

    _ep_suffix: str = "ui/files-actions-menu"

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register(self, name: str, display_name: str, callback_url: str, **kwargs) -> None:
        """Registers the files a dropdown menu element."""
        warnings.warn(
            "register() is deprecated and will be removed in a future version. Use register_ex() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "actionHandler": callback_url,
            "icon": kwargs.get("icon", ""),
            "mime": kwargs.get("mime", "file"),
            "permissions": kwargs.get("permissions", 31),
            "order": kwargs.get("order", 0),
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix}", json=params)

    async def register_ex(self, name: str, display_name: str, callback_url: str, **kwargs) -> None:
        """Registers the files dropdown menu element(extended version that receives ``ActionFileInfoEx``)."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "actionHandler": callback_url,
            "icon": kwargs.get("icon", ""),
            "mime": kwargs.get("mime", "file"),
            "permissions": kwargs.get("permissions", 31),
            "order": kwargs.get("order", 0),
        }
        await self._session.ocs("POST", f"{self._session.ae_url_v2}/{self._ep_suffix}", json=params)

    async def unregister(self, name: str, not_fail=True) -> None:
        """Removes files dropdown menu element."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{self._ep_suffix}", json={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_entry(self, name: str) -> UiFileActionEntry | None:
        """Get information of the file action meny entry for current app."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return UiFileActionEntry(
                await self._session.ocs("GET", f"{self._session.ae_url}/{self._ep_suffix}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None
