"""Nextcloud API for working with applications."""

from dataclasses import dataclass
from typing import Optional

from .._misc import require_capabilities
from .._session import NcSessionBasic


@dataclass
class ExAppInfo:
    """Information about the External Application."""

    app_id: str
    """`ID` of the application"""
    name: str
    """Display name"""
    version: str
    """Version of the application"""
    enabled: bool
    """Flag indicating if the application enabled"""
    last_check_time: int
    """UTC time of last successful application check"""
    system: bool
    """Flag indicating if the application is a system application"""

    def __init__(self, raw_data: dict):
        self.app_id = raw_data["id"]
        self.name = raw_data["name"]
        self.version = raw_data["version"]
        self.enabled = bool(raw_data["enabled"])
        self.last_check_time = raw_data["last_check_time"]
        self.system = raw_data["system"]


class AppsAPI:
    """The class provides the application management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/cloud/apps"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def disable(self, app_id: str) -> None:
        """Disables the application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        self._session.ocs(method="DELETE", path=f"{self._ep_base}/{app_id}")

    def enable(self, app_id: str) -> None:
        """Enables the application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        self._session.ocs(method="POST", path=f"{self._ep_base}/{app_id}")

    def get_list(self, enabled: Optional[bool] = None) -> list[str]:
        """Get the list of installed applications.

        :param enabled: filter to list all/only enabled/only disabled applications.
        """
        params = None
        if enabled is not None:
            params = {"filter": "enabled" if enabled else "disabled"}
        result = self._session.ocs(method="GET", path=self._ep_base, params=params)
        return list(result["apps"].values()) if isinstance(result["apps"], dict) else result["apps"]

    def is_installed(self, app_id: str) -> bool:
        """Returns ``True`` if specified application is installed."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in self.get_list()

    def is_enabled(self, app_id: str) -> bool:
        """Returns ``True`` if specified application is enabled."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in self.get_list(enabled=True)

    def is_disabled(self, app_id: str) -> bool:
        """Returns ``True`` if specified application is disabled."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in self.get_list(enabled=False)

    def ex_app_disable(self, app_id: str) -> None:
        """Disables the external application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        self._session.ocs(method="PUT", path=f"{self._session.ae_url}/ex-app/{app_id}/enabled", json={"enabled": 0})

    def ex_app_enable(self, app_id: str) -> None:
        """Enables the external application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        self._session.ocs(method="PUT", path=f"{self._session.ae_url}/ex-app/{app_id}/enabled", json={"enabled": 1})

    def ex_app_get_list(self, enabled: bool = False) -> list[ExAppInfo]:
        """Gets information of the enabled external applications installed on the server.

        :param enabled: Flag indicating whether to return only enabled applications or all applications.
            Default = **False**.
        """
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        url_param = "enabled" if enabled else "all"
        r = self._session.ocs(method="GET", path=f"{self._session.ae_url}/ex-app/{url_param}")
        return [ExAppInfo(i) for i in r]

    def ex_app_is_enabled(self, app_id: str) -> bool:
        """Returns ``True`` if specified external application is enabled."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in [i.app_id for i in self.ex_app_get_list(True)]

    def ex_app_is_disabled(self, app_id: str) -> bool:
        """Returns ``True`` if specified external application is disabled."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in [i.app_id for i in self.ex_app_get_list() if not i.enabled]
