"""Nextcloud API for working with apps V2's storage w/wo user context(table oc_appconfig_ex/oc_preferences_ex)."""

import dataclasses

from ._exceptions import NextcloudExceptionNotFound
from ._misc import require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class CfgRecord:
    """A representation of a single key-value pair returned from the **get_values** method."""

    key: str
    value: str

    def __init__(self, raw_data: dict):
        self.key = raw_data["configkey"]
        self.value = raw_data["configvalue"]


class _BasicAppCfgPref:
    _url_suffix: str

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_value(self, key: str, default=None) -> str | None:
        """Returns the value of the key, if found, or the specified default value."""
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", self._session.capabilities)
        r = self.get_values([key])
        if r:
            return r[0].value
        return default

    def get_values(self, keys: list[str]) -> list[CfgRecord]:
        """Returns the :py:class:`CfgRecord` for each founded key."""
        if not keys:
            return []
        if not all(keys):
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", self._session.capabilities)
        data = {"configKeys": keys}
        results = self._session.ocs("POST", f"{self._session.ae_url}/{self._url_suffix}/get-values", json=data)
        return [CfgRecord(i) for i in results]

    def delete(self, keys: str | list[str], not_fail=True) -> None:
        """Deletes config/preference entries by the provided keys."""
        if isinstance(keys, str):
            keys = [keys]
        if not keys:
            return
        if not all(keys):
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{self._url_suffix}", json={"configKeys": keys})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None


class _AsyncBasicAppCfgPref:
    _url_suffix: str

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    async def get_value(self, key: str, default=None) -> str | None:
        """Returns the value of the key, if found, or the specified default value."""
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", await self._session.capabilities)
        r = await self.get_values([key])
        if r:
            return r[0].value
        return default

    async def get_values(self, keys: list[str]) -> list[CfgRecord]:
        """Returns the :py:class:`CfgRecord` for each founded key."""
        if not keys:
            return []
        if not all(keys):
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", await self._session.capabilities)
        data = {"configKeys": keys}
        results = await self._session.ocs("POST", f"{self._session.ae_url}/{self._url_suffix}/get-values", json=data)
        return [CfgRecord(i) for i in results]

    async def delete(self, keys: str | list[str], not_fail=True) -> None:
        """Deletes config/preference entries by the provided keys."""
        if isinstance(keys, str):
            keys = [keys]
        if not keys:
            return
        if not all(keys):
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{self._url_suffix}", json={"configKeys": keys})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None


class PreferencesExAPI(_BasicAppCfgPref):
    """User specific preferences API, avalaible as **nc.preferences_ex.<method>**."""

    _url_suffix = "ex-app/preference"

    def set_value(self, key: str, value: str) -> None:
        """Sets a value for a key."""
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", self._session.capabilities)
        params = {"configKey": key, "configValue": value}
        self._session.ocs("POST", f"{self._session.ae_url}/{self._url_suffix}", json=params)


class AsyncPreferencesExAPI(_AsyncBasicAppCfgPref):
    """User specific preferences API."""

    _url_suffix = "ex-app/preference"

    async def set_value(self, key: str, value: str) -> None:
        """Sets a value for a key."""
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", await self._session.capabilities)
        params = {"configKey": key, "configValue": value}
        await self._session.ocs("POST", f"{self._session.ae_url}/{self._url_suffix}", json=params)


class AppConfigExAPI(_BasicAppCfgPref):
    """Non-user(App) specific preferences API, avalaible as **nc.appconfig_ex.<method>**."""

    _url_suffix = "ex-app/config"

    def set_value(self, key: str, value: str, sensitive: bool | None = None) -> None:
        """Sets a value and if specified the sensitive flag for a key.

        .. note:: A sensitive flag ensures key values are truncated in Nextcloud logs.
            Default for new records is ``False`` when sensitive is *unspecified*, if changes existing record and
            sensitive is *unspecified* it will not change the existing `sensitive` flag.
        """
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", self._session.capabilities)
        params: dict = {"configKey": key, "configValue": value}
        if sensitive is not None:
            params["sensitive"] = sensitive
        self._session.ocs("POST", f"{self._session.ae_url}/{self._url_suffix}", json=params)


class AsyncAppConfigExAPI(_AsyncBasicAppCfgPref):
    """Non-user(App) specific preferences API."""

    _url_suffix = "ex-app/config"

    async def set_value(self, key: str, value: str, sensitive: bool | None = None) -> None:
        """Sets a value and if specified the sensitive flag for a key.

        .. note:: A sensitive flag ensures key values are truncated in Nextcloud logs.
            Default for new records is ``False`` when sensitive is *unspecified*, if changes existing record and
            sensitive is *unspecified* it will not change the existing `sensitive` flag.
        """
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", await self._session.capabilities)
        params: dict = {"configKey": key, "configValue": value}
        if sensitive is not None:
            params["sensitive"] = sensitive
        await self._session.ocs("POST", f"{self._session.ae_url}/{self._url_suffix}", json=params)
