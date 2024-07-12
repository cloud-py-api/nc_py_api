"""Nextcloud API for working with applications."""

import dataclasses
import datetime

from ._misc import require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class ExAppInfo:
    """Information about the External Application."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def app_id(self) -> str:
        """`ID` of the application."""
        return self._raw_data["id"]

    @property
    def name(self) -> str:
        """Display name."""
        return self._raw_data["name"]

    @property
    def version(self) -> str:
        """Version of the application."""
        return self._raw_data["version"]

    @property
    def enabled(self) -> bool:
        """Flag indicating if the application enabled."""
        return bool(self._raw_data["enabled"])

    @property
    def last_check_time(self) -> datetime.datetime:
        """Time of the last successful application check."""
        return datetime.datetime.utcfromtimestamp(int(self._raw_data["last_check_time"])).replace(
            tzinfo=datetime.timezone.utc
        )

    @property
    def system(self) -> bool:
        """**DEPRECATED** Flag indicating if the application is a system application."""
        return True

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.app_id}, ver={self.version}>"


class _AppsAPI:
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
        self._session.ocs("DELETE", f"{self._ep_base}/{app_id}")

    def enable(self, app_id: str) -> None:
        """Enables the application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        self._session.ocs("POST", f"{self._ep_base}/{app_id}")

    def get_list(self, enabled: bool | None = None) -> list[str]:
        """Get the list of installed applications.

        :param enabled: filter to list all/only enabled/only disabled applications.
        """
        params = None
        if enabled is not None:
            params = {"filter": "enabled" if enabled else "disabled"}
        result = self._session.ocs("GET", self._ep_base, params=params)
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
        self._session.ocs("PUT", f"{self._session.ae_url}/ex-app/{app_id}/enabled", json={"enabled": 0})

    def ex_app_enable(self, app_id: str) -> None:
        """Enables the external application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        self._session.ocs("PUT", f"{self._session.ae_url}/ex-app/{app_id}/enabled", json={"enabled": 1})

    def ex_app_get_list(self, enabled: bool = False) -> list[ExAppInfo]:
        """Gets information of the enabled external applications installed on the server.

        :param enabled: Flag indicating whether to return only enabled applications or all applications.
        """
        require_capabilities("app_api", self._session.capabilities)
        url_param = "enabled" if enabled else "all"
        r = self._session.ocs("GET", f"{self._session.ae_url}/ex-app/{url_param}")
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


class _AsyncAppsAPI:
    """The class provides the async application management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/cloud/apps"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    async def disable(self, app_id: str) -> None:
        """Disables the application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        await self._session.ocs("DELETE", f"{self._ep_base}/{app_id}")

    async def enable(self, app_id: str) -> None:
        """Enables the application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        await self._session.ocs("POST", f"{self._ep_base}/{app_id}")

    async def get_list(self, enabled: bool | None = None) -> list[str]:
        """Get the list of installed applications.

        :param enabled: filter to list all/only enabled/only disabled applications.
        """
        params = None
        if enabled is not None:
            params = {"filter": "enabled" if enabled else "disabled"}
        result = await self._session.ocs("GET", self._ep_base, params=params)
        return list(result["apps"].values()) if isinstance(result["apps"], dict) else result["apps"]

    async def is_installed(self, app_id: str) -> bool:
        """Returns ``True`` if specified application is installed."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in await self.get_list()

    async def is_enabled(self, app_id: str) -> bool:
        """Returns ``True`` if specified application is enabled."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in await self.get_list(enabled=True)

    async def is_disabled(self, app_id: str) -> bool:
        """Returns ``True`` if specified application is disabled."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in await self.get_list(enabled=False)

    async def ex_app_disable(self, app_id: str) -> None:
        """Disables the external application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        await self._session.ocs("PUT", f"{self._session.ae_url}/ex-app/{app_id}/enabled", json={"enabled": 0})

    async def ex_app_enable(self, app_id: str) -> None:
        """Enables the external application.

        .. note:: Does not work in NextcloudApp mode, only for Nextcloud client mode.
        """
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        await self._session.ocs("PUT", f"{self._session.ae_url}/ex-app/{app_id}/enabled", json={"enabled": 1})

    async def ex_app_get_list(self, enabled: bool = False) -> list[ExAppInfo]:
        """Gets information of the enabled external applications installed on the server.

        :param enabled: Flag indicating whether to return only enabled applications or all applications.
        """
        require_capabilities("app_api", await self._session.capabilities)
        url_param = "enabled" if enabled else "all"
        r = await self._session.ocs("GET", f"{self._session.ae_url}/ex-app/{url_param}")
        return [ExAppInfo(i) for i in r]

    async def ex_app_is_enabled(self, app_id: str) -> bool:
        """Returns ``True`` if specified external application is enabled."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in [i.app_id for i in await self.ex_app_get_list(True)]

    async def ex_app_is_disabled(self, app_id: str) -> bool:
        """Returns ``True`` if specified external application is disabled."""
        if not app_id:
            raise ValueError("`app_id` parameter can not be empty")
        return app_id in [i.app_id for i in await self.ex_app_get_list() if not i.enabled]
