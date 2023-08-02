"""Nextcloud API for working with apps V2's storage w/wo user context(table oc_appconfig_ex/oc_preferences_ex)."""
from dataclasses import dataclass
from typing import Optional, Union

from ._session import NcSessionBasic
from .constants import APP_V2_BASIC_URL
from .exceptions import NextcloudExceptionNotFound
from .misc import require_capabilities


@dataclass
class CfgRecord:
    key: str
    value: str

    def __init__(self, raw_data: dict):
        self.key = raw_data["configkey"]
        self.value = raw_data["configvalue"]


class BasicAppCfgPref:
    url_suffix: str

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_value(self, key: str, default=None) -> Optional[str]:
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        r = self.get_values([key])
        if r:
            return r[0].value
        return default

    def get_values(self, keys: list[str]) -> list[CfgRecord]:
        if not keys:
            return []
        if not all(keys):
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        data = {"configKeys": keys}
        results = self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}/get-values", json=data)
        return [CfgRecord(i) for i in results]

    def delete(self, keys: Union[str, list[str]], not_fail=True) -> None:
        if isinstance(keys, str):
            keys = [keys]
        if not keys:
            return
        if not all(keys):
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        try:
            self._session.ocs(method="DELETE", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}", json={"configKeys": keys})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None


class PreferencesExAPI(BasicAppCfgPref):
    url_suffix = "ex-app/preference"

    def set_value(self, key: str, value: str) -> None:
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        params = {"configKey": key, "configValue": value}
        self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}", json=params)


class AppConfigExAPI(BasicAppCfgPref):
    url_suffix = "ex-app/config"

    def set_value(self, key: str, value: str, sensitive: bool = False) -> None:
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        params: dict = {"configKey": key, "configValue": value}
        if sensitive:
            params["sensitive"] = True
        self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}", json=params)
