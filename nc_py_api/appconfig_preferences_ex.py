"""
Nextcloud API for working with apps V2's storage w/wo user context(table oc_appconfig_ex/oc_preferences_ex).
"""
from typing import Optional, TypedDict, Union

from ._session import NcSessionBasic
from .constants import APP_V2_BASIC_URL
from .exceptions import NextcloudExceptionNotFound
from .misc import require_capabilities


class AppCfgPrefRecord(TypedDict):
    configkey: str
    configvalue: str


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
            return r[0]["configvalue"]
        return default

    def get_values(self, keys: list[str]) -> list[AppCfgPrefRecord]:
        if not keys:
            return []
        if not all(keys):
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        data = {"configKeys": keys}
        return self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}/get-values", json=data)

    def set(self, key: str, value: str) -> None:
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        params = {"configKey": key, "configValue": value}
        self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}", json=params)

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


class AppConfigExAPI(BasicAppCfgPref):
    url_suffix = "ex-app/config"
