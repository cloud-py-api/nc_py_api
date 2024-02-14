"""Nextcloud API for declaring TextProcessing provider."""

import contextlib
import dataclasses

from ..._exceptions import NextcloudException, NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import AsyncNcSessionApp, NcSessionApp

_EP_SUFFIX: str = "ai_provider/text_processing"


@dataclasses.dataclass
class TextProcessingProvider:
    """TextProcessing provider description."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def name(self) -> str:
        """Unique ID for the provider."""
        return self._raw_data["name"]

    @property
    def display_name(self) -> str:
        """Providers display name."""
        return self._raw_data["display_name"]

    @property
    def action_handler(self) -> str:
        """Relative ExApp url which will be called by Nextcloud."""
        return self._raw_data["action_handler"]

    @property
    def task_type(self) -> str:
        """The TaskType provided by this provider."""
        return self._raw_data["task_type"]

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, type={self.task_type}, handler={self.action_handler}>"


class _TextProcessingProviderAPI:
    """API for TextProcessing providers, avalaible as **nc.providers.speech_to_text.<method>**."""

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(self, name: str, display_name: str, callback_url: str, task_type: str) -> None:
        """Registers or edit the TextProcessing provider."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "actionHandler": callback_url,
            "taskType": task_type,
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes TextProcessing provider."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_entry(self, name: str) -> TextProcessingProvider | None:
        """Get information of the TextProcessing."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return TextProcessingProvider(
                self._session.ocs("GET", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None

    def report_result(self, task_id: int, result: str = "", error: str = "") -> None:
        """Report results of the text processing to Nextcloud."""
        require_capabilities("app_api", self._session.capabilities)
        with contextlib.suppress(NextcloudException):
            self._session.ocs(
                "PUT",
                f"{self._session.ae_url}/{_EP_SUFFIX}",
                json={"taskId": task_id, "result": result, "error": error},
            )


class _AsyncTextProcessingProviderAPI:
    """Async API for TextProcessing providers."""

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register(self, name: str, display_name: str, callback_url: str, task_type: str) -> None:
        """Registers or edit the TextProcessing provider."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "actionHandler": callback_url,
            "taskType": task_type,
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    async def unregister(self, name: str, not_fail=True) -> None:
        """Removes TextProcessing provider."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_entry(self, name: str) -> TextProcessingProvider | None:
        """Get information of the TextProcessing."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return TextProcessingProvider(
                await self._session.ocs("GET", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None

    async def report_result(self, task_id: int, result: str = "", error: str = "") -> None:
        """Report results of the text processing to Nextcloud."""
        require_capabilities("app_api", await self._session.capabilities)
        with contextlib.suppress(NextcloudException):
            await self._session.ocs(
                "PUT",
                f"{self._session.ae_url}/{_EP_SUFFIX}",
                json={"taskId": task_id, "result": result, "error": error},
            )
