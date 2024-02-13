"""API for adding scripts, styles, initial-states to the Nextcloud UI."""

import dataclasses

from ..._exceptions import NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import AsyncNcSessionApp, NcSessionApp


@dataclasses.dataclass
class UiBase:
    """Basic class for InitialStates, Scripts, Styles."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def appid(self) -> str:
        """The App ID of the owner of this UI."""
        return self._raw_data["appid"]

    @property
    def ui_type(self) -> str:
        """UI type. Possible values: 'top_menu'."""
        return self._raw_data["type"]

    @property
    def name(self) -> str:
        """UI page name, acts like ID."""
        return self._raw_data["name"]


class UiInitState(UiBase):
    """One Initial State description."""

    @property
    def key(self) -> str:
        """Name of the object."""
        return self._raw_data["key"]

    @property
    def value(self) -> dict | list:
        """Object for the page(template)."""
        return self._raw_data["value"]

    def __repr__(self):
        return f"<{self.__class__.__name__} type={self.ui_type}, name={self.name}, key={self.key}>"


class UiScript(UiBase):
    """One Script description."""

    @property
    def path(self) -> str:
        """Url to script relative to the ExApp."""
        return self._raw_data["path"]

    @property
    def after_app_id(self) -> str:
        """Optional AppID after which script should be injected."""
        return self._raw_data["after_app_id"] if self._raw_data["after_app_id"] else ""

    def __repr__(self):
        return f"<{self.__class__.__name__} type={self.ui_type}, name={self.name}, path={self.path}>"


class UiStyle(UiBase):
    """One Style description."""

    @property
    def path(self) -> str:
        """Url to style relative to the ExApp."""
        return self._raw_data["path"]

    def __repr__(self):
        return f"<{self.__class__.__name__} type={self.ui_type}, name={self.name}, path={self.path}>"


class _UiResources:
    """API for adding scripts, styles, initial-states to the pages, avalaible as **nc.ui.resources.<method>**."""

    _ep_suffix_init_state: str = "ui/initial-state"
    _ep_suffix_js: str = "ui/script"
    _ep_suffix_css: str = "ui/style"

    def __init__(self, session: NcSessionApp):
        self._session = session

    def set_initial_state(self, ui_type: str, name: str, key: str, value: dict | list) -> None:
        """Add or update initial state for the page(template)."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "type": ui_type,
            "name": name,
            "key": key,
            "value": value,
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix_init_state}", json=params)

    def delete_initial_state(self, ui_type: str, name: str, key: str, not_fail=True) -> None:
        """Removes initial state for the page(template) by object name."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs(
                "DELETE",
                f"{self._session.ae_url}/{self._ep_suffix_init_state}",
                params={"type": ui_type, "name": name, "key": key},
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_initial_state(self, ui_type: str, name: str, key: str) -> UiInitState | None:
        """Get information about initial state for the page(template) by object name."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return UiInitState(
                self._session.ocs(
                    "GET",
                    f"{self._session.ae_url}/{self._ep_suffix_init_state}",
                    params={"type": ui_type, "name": name, "key": key},
                )
            )
        except NextcloudExceptionNotFound:
            return None

    def set_script(self, ui_type: str, name: str, path: str, after_app_id: str = "") -> None:
        """Add or update script for the page(template)."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "type": ui_type,
            "name": name,
            "path": path,
            "afterAppId": after_app_id,
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix_js}", json=params)

    def delete_script(self, ui_type: str, name: str, path: str, not_fail=True) -> None:
        """Removes script for the page(template) by object name."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs(
                "DELETE",
                f"{self._session.ae_url}/{self._ep_suffix_js}",
                params={"type": ui_type, "name": name, "path": path},
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_script(self, ui_type: str, name: str, path: str) -> UiScript | None:
        """Get information about script for the page(template) by object name."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return UiScript(
                self._session.ocs(
                    "GET",
                    f"{self._session.ae_url}/{self._ep_suffix_js}",
                    params={"type": ui_type, "name": name, "path": path},
                )
            )
        except NextcloudExceptionNotFound:
            return None

    def set_style(self, ui_type: str, name: str, path: str) -> None:
        """Add or update style(css) for the page(template)."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "type": ui_type,
            "name": name,
            "path": path,
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix_css}", json=params)

    def delete_style(self, ui_type: str, name: str, path: str, not_fail=True) -> None:
        """Removes style(css) for the page(template) by object name."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs(
                "DELETE",
                f"{self._session.ae_url}/{self._ep_suffix_css}",
                params={"type": ui_type, "name": name, "path": path},
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_style(self, ui_type: str, name: str, path: str) -> UiStyle | None:
        """Get information about style(css) for the page(template) by object name."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return UiStyle(
                self._session.ocs(
                    "GET",
                    f"{self._session.ae_url}/{self._ep_suffix_css}",
                    params={"type": ui_type, "name": name, "path": path},
                )
            )
        except NextcloudExceptionNotFound:
            return None


class _AsyncUiResources:
    """Async API for adding scripts, styles, initial-states to the TopMenu pages."""

    _ep_suffix_init_state: str = "ui/initial-state"
    _ep_suffix_js: str = "ui/script"
    _ep_suffix_css: str = "ui/style"

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def set_initial_state(self, ui_type: str, name: str, key: str, value: dict | list) -> None:
        """Add or update initial state for the page(template)."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "type": ui_type,
            "name": name,
            "key": key,
            "value": value,
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix_init_state}", json=params)

    async def delete_initial_state(self, ui_type: str, name: str, key: str, not_fail=True) -> None:
        """Removes initial state for the page(template) by object name."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs(
                "DELETE",
                f"{self._session.ae_url}/{self._ep_suffix_init_state}",
                params={"type": ui_type, "name": name, "key": key},
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_initial_state(self, ui_type: str, name: str, key: str) -> UiInitState | None:
        """Get information about initial state for the page(template) by object name."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return UiInitState(
                await self._session.ocs(
                    "GET",
                    f"{self._session.ae_url}/{self._ep_suffix_init_state}",
                    params={"type": ui_type, "name": name, "key": key},
                )
            )
        except NextcloudExceptionNotFound:
            return None

    async def set_script(self, ui_type: str, name: str, path: str, after_app_id: str = "") -> None:
        """Add or update script for the page(template)."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "type": ui_type,
            "name": name,
            "path": path,
            "afterAppId": after_app_id,
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix_js}", json=params)

    async def delete_script(self, ui_type: str, name: str, path: str, not_fail=True) -> None:
        """Removes script for the page(template) by object name."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs(
                "DELETE",
                f"{self._session.ae_url}/{self._ep_suffix_js}",
                params={"type": ui_type, "name": name, "path": path},
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_script(self, ui_type: str, name: str, path: str) -> UiScript | None:
        """Get information about script for the page(template) by object name."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return UiScript(
                await self._session.ocs(
                    "GET",
                    f"{self._session.ae_url}/{self._ep_suffix_js}",
                    params={"type": ui_type, "name": name, "path": path},
                )
            )
        except NextcloudExceptionNotFound:
            return None

    async def set_style(self, ui_type: str, name: str, path: str) -> None:
        """Add or update style(css) for the page(template)."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "type": ui_type,
            "name": name,
            "path": path,
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{self._ep_suffix_css}", json=params)

    async def delete_style(self, ui_type: str, name: str, path: str, not_fail=True) -> None:
        """Removes style(css) for the page(template) by object name."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs(
                "DELETE",
                f"{self._session.ae_url}/{self._ep_suffix_css}",
                params={"type": ui_type, "name": name, "path": path},
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_style(self, ui_type: str, name: str, path: str) -> UiStyle | None:
        """Get information about style(css) for the page(template) by object name."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return UiStyle(
                await self._session.ocs(
                    "GET",
                    f"{self._session.ae_url}/{self._ep_suffix_css}",
                    params={"type": ui_type, "name": name, "path": path},
                )
            )
        except NextcloudExceptionNotFound:
            return None
