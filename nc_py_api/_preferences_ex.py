"""Nextcloud API for working with apps V2's storage w/wo user context(table oc_appconfig_ex/oc_preferences_ex)."""
import dataclasses
import typing

from ._exceptions import NextcloudExceptionNotFound
from ._misc import require_capabilities
from ._session import NcSessionBasic


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

    def get_value(self, key: str, default=None) -> typing.Optional[str]:
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
        results = self._session.ocs(
            method="POST", path=f"{self._session.ae_url}/{self._url_suffix}/get-values", json=data
        )
        return [CfgRecord(i) for i in results]

    def delete(self, keys: typing.Union[str, list[str]], not_fail=True) -> None:
        """Deletes config/preference entries by the provided keys."""
        if isinstance(keys, str):
            keys = [keys]
        if not keys:
            return
        if not all(keys):
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs(
                method="DELETE", path=f"{self._session.ae_url}/{self._url_suffix}", json={"configKeys": keys}
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None


class PreferencesExAPI(_BasicAppCfgPref):
    """User specific preferences API."""

    _url_suffix = "ex-app/preference"

    def set_value(self, key: str, value: str) -> None:
        """Sets a value for a key."""
        if not key:
            raise ValueError("`key` parameter can not be empty")
        require_capabilities("app_api", self._session.capabilities)
        params = {"configKey": key, "configValue": value}
        self._session.ocs(method="POST", path=f"{self._session.ae_url}/{self._url_suffix}", json=params)


class AppConfigExAPI(_BasicAppCfgPref):
    """Non-user(App) specific preferences API."""

    _url_suffix = "ex-app/config"

    def set_value(self, key: str, value: str, sensitive: typing.Optional[bool] = None) -> None:
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
        self._session.ocs(method="POST", path=f"{self._session.ae_url}/{self._url_suffix}", json=params)
