"""Nextcloud API for declaring Translations provider."""

import contextlib
import dataclasses

from ..._exceptions import NextcloudException, NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import AsyncNcSessionApp, NcSessionApp

_EP_SUFFIX: str = "ai_provider/translation"


@dataclasses.dataclass
class TranslationsProvider:
    """Translations provider description."""

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
    def from_languages(self) -> dict[str, str]:
        """Input languages supported by provider."""
        return self._raw_data["from_languages"]

    @property
    def to_languages(self) -> dict[str, str]:
        """Output languages supported by provider."""
        return self._raw_data["to_languages"]

    @property
    def action_handler(self) -> str:
        """Relative ExApp url which will be called by Nextcloud."""
        return self._raw_data["action_handler"]

    @property
    def action_handler_detect_lang(self) -> str:
        """Relative ExApp url which will be called by Nextcloud to detect language."""
        return self._raw_data.get("action_detect_lang", "")

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, handler={self.action_handler}>"


class _TranslationsProviderAPI:
    """API for Translations providers, avalaible as **nc.providers.translations.<method>**."""

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(
        self,
        name: str,
        display_name: str,
        callback_url: str,
        from_languages: dict[str, str],
        to_languages: dict[str, str],
        detect_lang_callback_url: str = "",
    ) -> None:
        """Registers or edit the Translations provider."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "fromLanguages": from_languages,
            "toLanguages": to_languages,
            "actionHandler": callback_url,
            "actionDetectLang": detect_lang_callback_url,
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes Translations provider."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_entry(self, name: str) -> TranslationsProvider | None:
        """Get information of the TranslationsProvider."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return TranslationsProvider(
                self._session.ocs("GET", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None

    def report_result(self, task_id: int, result: str = "", error: str = "") -> None:
        """Report results of translation task to Nextcloud."""
        require_capabilities("app_api", self._session.capabilities)
        with contextlib.suppress(NextcloudException):
            self._session.ocs(
                "PUT",
                f"{self._session.ae_url}/{_EP_SUFFIX}",
                json={"taskId": task_id, "result": result, "error": error},
            )


class _AsyncTranslationsProviderAPI:
    """Async API for Translations providers."""

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register(
        self,
        name: str,
        display_name: str,
        callback_url: str,
        from_languages: dict[str, str],
        to_languages: dict[str, str],
        detect_lang_callback_url: str = "",
    ) -> None:
        """Registers or edit the Translations provider."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "fromLanguages": from_languages,
            "toLanguages": to_languages,
            "actionHandler": callback_url,
            "actionDetectLang": detect_lang_callback_url,
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    async def unregister(self, name: str, not_fail=True) -> None:
        """Removes Translations provider."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_entry(self, name: str) -> TranslationsProvider | None:
        """Get information of the TranslationsProvider."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return TranslationsProvider(
                await self._session.ocs("GET", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
            )
        except NextcloudExceptionNotFound:
            return None

    async def report_result(self, task_id: int, result: str = "", error: str = "") -> None:
        """Report results of translation task to Nextcloud."""
        require_capabilities("app_api", await self._session.capabilities)
        with contextlib.suppress(NextcloudException):
            await self._session.ocs(
                "PUT",
                f"{self._session.ae_url}/{_EP_SUFFIX}",
                json={"taskId": task_id, "result": result, "error": error},
            )
