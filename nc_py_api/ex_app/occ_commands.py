"""Nextcloud API for registering OCC commands for ExApps."""

import dataclasses

from .._exceptions import NextcloudExceptionNotFound
from .._misc import clear_from_params_empty, require_capabilities
from .._session import AsyncNcSessionApp, NcSessionApp

_EP_SUFFIX: str = "occ_command"


@dataclasses.dataclass
class OccCommand:
    """OccCommand description."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def name(self) -> str:
        """Unique ID for the command."""
        return self._raw_data["name"]

    @property
    def description(self) -> str:
        """Command description."""
        return self._raw_data["description"]

    @property
    def hidden(self) -> bool:
        """Flag determining ss command hidden or not."""
        return bool(self._raw_data["hidden"])

    @property
    def arguments(self) -> dict:
        """Look at PHP Symfony framework for details."""
        return self._raw_data["arguments"]

    @property
    def options(self) -> str:
        """Look at PHP Symfony framework for details."""
        return self._raw_data["options"]

    @property
    def usages(self) -> str:
        """Look at PHP Symfony framework for details."""
        return self._raw_data["usages"]

    @property
    def action_handler(self) -> str:
        """Relative ExApp url which will be called by Nextcloud."""
        return self._raw_data["execute_handler"]

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, handler={self.action_handler}>"


class OccCommandsAPI:
    """API for registering OCC commands, avalaible as **nc.occ_command.<method>**."""

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(
        self,
        name: str,
        callback_url: str,
        arguments: list | None = None,
        options: list | None = None,
        usages: list | None = None,
        description: str = "",
        hidden: bool = False,
    ) -> None:
        """Registers or edit the OCC command."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "name": name,
            "description": description,
            "arguments": arguments,
            "hidden": int(hidden),
            "options": options,
            "usages": usages,
            "execute_handler": callback_url,
        }
        clear_from_params_empty(["arguments", "options", "usages"], params)
        self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes the OCC command."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_entry(self, name: str) -> OccCommand | None:
        """Get information of the OCC command."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return OccCommand(self._session.ocs("GET", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name}))
        except NextcloudExceptionNotFound:
            return None


class AsyncOccCommandsAPI:
    """Async API for registering OCC commands, avalaible as **nc.occ_command.<method>**."""

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register(
        self,
        name: str,
        callback_url: str,
        arguments: list | None = None,
        options: list | None = None,
        usages: list | None = None,
        description: str = "",
        hidden: bool = False,
    ) -> None:
        """Registers or edit the OCC command."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "name": name,
            "description": description,
            "arguments": arguments,
            "hidden": int(hidden),
            "options": options,
            "usages": usages,
            "execute_handler": callback_url,
        }
        clear_from_params_empty(["arguments", "options", "usages"], params)
        await self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    async def unregister(self, name: str, not_fail=True) -> None:
        """Removes the OCC command."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_entry(self, name: str) -> OccCommand | None:
        """Get information of the OCC command."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return OccCommand(
                await self._session.ocs("GET", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None
