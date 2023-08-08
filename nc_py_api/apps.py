"""Nextcloud API for working with applications."""

from typing import Optional, TypedDict

from ._session import NcSessionBasic
from .misc import require_capabilities

ENDPOINT = "/ocs/v1.php/cloud/apps"


class ExAppInfo(TypedDict):
    """Information about the External Application."""

    id: str
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


class AppAPI:
    """The class provides the application management API on the Nextcloud server."""

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def disable(self, app_id: str) -> None:
        """Disables the application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{app_id}")

    def enable(self, app_id: str) -> None:
        """Enables the application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        self._session.ocs(method="POST", path=f"{ENDPOINT}/{app_id}")

    def get_list(self, enabled: Optional[bool] = None) -> list[str]:
        """Get the list of installed applications.

        :param enabled: filter to list all/only enabled/only disabled applications.
        """
        params = None
        if enabled is not None:
            params = {"filter": "enabled" if enabled else "disabled"}
        result = self._session.ocs(method="GET", path=ENDPOINT, params=params)
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

    def ex_app_get_list(self) -> list[str]:
        """Gets the list of the external applications IDs installed on the server."""
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        return self._session.ocs(method="GET", path=f"{self._session.ae_url}/ex-app/all", params={"extended": 0})

    def ex_app_get_info(self) -> list[ExAppInfo]:
        """Gets information of the external applications installed on the server."""
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        return self._session.ocs(method="GET", path=f"{self._session.ae_url}/ex-app/all", params={"extended": 1})
