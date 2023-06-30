"""
Nextcloud API for working with applications.
"""

from typing import Optional

from ._session import NcSessionBasic

ENDPOINT = "/ocs/v1.php/cloud/apps"


class AppAPI:
    def __init__(self, session: NcSessionBasic):
        self._session = session

    def disable(self, app_name: str) -> None:
        if not app_name:
            raise ValueError("`app_name` parameter can not be empty")
        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{app_name}")

    def enable(self, app_name: str) -> None:
        if not app_name:
            raise ValueError("`app_name` parameter can not be empty")
        self._session.ocs(method="POST", path=f"{ENDPOINT}/{app_name}")

    def list(self, enabled: Optional[bool] = None) -> list[str]:
        params = None
        if enabled is not None:
            params = {"filter": "enabled" if enabled else "disabled"}
        result = self._session.ocs(method="GET", path=ENDPOINT, params=params)
        return list(result["apps"].values()) if isinstance(result["apps"], dict) else result["apps"]

    def is_installed(self, app_name: str) -> bool:
        if not app_name:
            raise ValueError("`app_name` parameter can not be empty")
        return app_name in self.list()

    def is_enabled(self, app_name: str) -> bool:
        if not app_name:
            raise ValueError("`app_name` parameter can not be empty")
        return app_name in self.list(enabled=True)

    def is_disabled(self, app_name: str) -> bool:
        if not app_name:
            raise ValueError("`app_name` parameter can not be empty")
        return app_name in self.list(enabled=False)
