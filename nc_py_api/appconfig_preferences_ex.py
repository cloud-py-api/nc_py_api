"""
Nextcloud API for working with apps V2's storage w/wo user context(table oc_appconfig_ex/oc_preferences_ex).
"""
from typing import Optional, TypedDict, Union

from ._session import NcSessionBasic
from .constants import APP_V2_BASIC_URL
from .misc import require_capabilities


class AppCfgPrefRecord(TypedDict):
    configkey: str
    configvalue: str


class BasicAppCfgPref:
    url_suffix: str

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_value(self, key: str) -> Optional[str]:
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        r = self.get_values([key])
        if r:
            return r[0]["configvalue"]
        return None

    def get_values(self, keys: list[str]) -> list[AppCfgPrefRecord]:
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        data = {"configKeys": keys}
        return self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}/get-values", json=data)

    def set(self, key: str, value: str) -> None:
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        params = {"configKey": key, "configValue": value}
        self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}", json=params)

    def delete(self, keys: Union[str, list[str]]) -> None:
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        if isinstance(keys, str):
            keys = [keys]
        self._session.ocs(method="DELETE", path=f"{APP_V2_BASIC_URL}/{self.url_suffix}", json={"configKeys": keys})


class PreferencesExAPI(BasicAppCfgPref):
    url_suffix = "ex-app/preference"


class AppConfigExAPI(BasicAppCfgPref):
    url_suffix = "ex-app/config"
