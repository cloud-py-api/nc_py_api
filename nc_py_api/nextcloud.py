"""Nextcloud class providing access to all API endpoints."""

import typing
from abc import ABC

from fastapi import Request as FastAPIRequest
from httpx import Headers

from ._exceptions import NextcloudExceptionNotFound
from ._misc import check_capabilities, require_capabilities
from ._preferences import AsyncPreferencesAPI, PreferencesAPI
from ._preferences_ex import (
    AppConfigExAPI,
    AsyncAppConfigExAPI,
    AsyncPreferencesExAPI,
    PreferencesExAPI,
)
from ._session import (
    AppConfig,
    AsyncNcSession,
    AsyncNcSessionApp,
    AsyncNcSessionBasic,
    NcSession,
    NcSessionApp,
    NcSessionBasic,
    ServerVersion,
)
from ._talk_api import _AsyncTalkAPI, _TalkAPI
from ._theming import ThemingInfo, get_parsed_theme
from .activity import _ActivityAPI, _AsyncActivityAPI
from .apps import _AppsAPI, _AsyncAppsAPI
from .calendar import _CalendarAPI
from .ex_app.defs import ApiScope, LogLvl
from .ex_app.ui.ui import AsyncUiApi, UiApi
from .files.files import AsyncFilesAPI, FilesAPI
from .notes import _AsyncNotesAPI, _NotesAPI
from .notifications import _AsyncNotificationsAPI, _NotificationsAPI
from .user_status import _AsyncUserStatusAPI, _UserStatusAPI
from .users import _AsyncUsersAPI, _UsersAPI
from .users_groups import _AsyncUsersGroupsAPI, _UsersGroupsAPI
from .weather_status import _AsyncWeatherStatusAPI, _WeatherStatusAPI


class _NextcloudBasic(ABC):  # pylint: disable=too-many-instance-attributes
    apps: _AppsAPI
    """Nextcloud API for App management"""
    activity: _ActivityAPI
    """Activity Application API"""
    cal: _CalendarAPI
    """Nextcloud Calendar API"""
    files: FilesAPI
    """Nextcloud API for File System and Files Sharing"""
    preferences: PreferencesAPI
    """Nextcloud User Preferences API"""
    notes: _NotesAPI
    """Nextcloud Notes API"""
    notifications: _NotificationsAPI
    """Nextcloud API for managing user notifications"""
    talk: _TalkAPI
    """Nextcloud Talk API"""
    users: _UsersAPI
    """Nextcloud API for managing users."""
    users_groups: _UsersGroupsAPI
    """Nextcloud API for managing user groups."""
    user_status: _UserStatusAPI
    """Nextcloud API for managing users statuses"""
    weather_status: _WeatherStatusAPI
    """Nextcloud API for managing user weather statuses"""
    _session: NcSessionBasic

    def __init__(self, session: NcSessionBasic):
        self.apps = _AppsAPI(session)
        self.activity = _ActivityAPI(session)
        self.cal = _CalendarAPI(session)
        self.files = FilesAPI(session)
        self.preferences = PreferencesAPI(session)
        self.notes = _NotesAPI(session)
        self.notifications = _NotificationsAPI(session)
        self.talk = _TalkAPI(session)
        self.users = _UsersAPI(session)
        self.users_groups = _UsersGroupsAPI(session)
        self.user_status = _UserStatusAPI(session)
        self.weather_status = _WeatherStatusAPI(session)

    @property
    def capabilities(self) -> dict:
        """Returns the capabilities of the Nextcloud instance."""
        return self._session.capabilities

    @property
    def srv_version(self) -> ServerVersion:
        """Returns dictionary with the server version."""
        return self._session.nc_version

    def check_capabilities(self, capabilities: str | list[str]) -> list[str]:
        """Returns the list with missing capabilities if any."""
        return check_capabilities(capabilities, self.capabilities)

    def update_server_info(self) -> None:
        """Updates the capabilities and the Nextcloud version.

        *In normal cases, it is called automatically and there is no need to call it manually.*
        """
        self._session.update_server_info()

    @property
    def response_headers(self) -> Headers:
        """Returns the `HTTPX headers <https://www.python-httpx.org/api/#headers>`_ from the last response."""
        return self._session.response_headers

    @property
    def theme(self) -> ThemingInfo | None:
        """Returns Theme information."""
        return get_parsed_theme(self.capabilities["theming"]) if "theming" in self.capabilities else None

    def ocs(
        self,
        method: str,
        path: str,
        *,
        content: bytes | str | typing.Iterable[bytes] | typing.AsyncIterable[bytes] | None = None,
        json: dict | list | None = None,
        params: dict | None = None,
        **kwargs,
    ):
        """Performs OCS call and returns OCS response payload data."""
        return self._session.ocs(method, path, content=content, json=json, params=params, **kwargs)


class _AsyncNextcloudBasic(ABC):  # pylint: disable=too-many-instance-attributes
    apps: _AsyncAppsAPI
    """Nextcloud API for App management"""
    activity: _AsyncActivityAPI
    """Activity Application API"""
    # cal: _CalendarAPI
    # """Nextcloud Calendar API"""
    files: AsyncFilesAPI
    """Nextcloud API for File System and Files Sharing"""
    preferences: AsyncPreferencesAPI
    """Nextcloud User Preferences API"""
    notes: _AsyncNotesAPI
    """Nextcloud Notes API"""
    notifications: _AsyncNotificationsAPI
    """Nextcloud API for managing user notifications"""
    talk: _AsyncTalkAPI
    """Nextcloud Talk API"""
    users: _AsyncUsersAPI
    """Nextcloud API for managing users."""
    users_groups: _AsyncUsersGroupsAPI
    """Nextcloud API for managing user groups."""
    user_status: _AsyncUserStatusAPI
    """Nextcloud API for managing users statuses"""
    weather_status: _AsyncWeatherStatusAPI
    """Nextcloud API for managing user weather statuses"""
    _session: AsyncNcSessionBasic

    def __init__(self, session: AsyncNcSessionBasic):
        self.apps = _AsyncAppsAPI(session)
        self.activity = _AsyncActivityAPI(session)
        # self.cal = _CalendarAPI(session)
        self.files = AsyncFilesAPI(session)
        self.preferences = AsyncPreferencesAPI(session)
        self.notes = _AsyncNotesAPI(session)
        self.notifications = _AsyncNotificationsAPI(session)
        self.talk = _AsyncTalkAPI(session)
        self.users = _AsyncUsersAPI(session)
        self.users_groups = _AsyncUsersGroupsAPI(session)
        self.user_status = _AsyncUserStatusAPI(session)
        self.weather_status = _AsyncWeatherStatusAPI(session)

    @property
    async def capabilities(self) -> dict:
        """Returns the capabilities of the Nextcloud instance."""
        return await self._session.capabilities

    @property
    async def srv_version(self) -> ServerVersion:
        """Returns dictionary with the server version."""
        return await self._session.nc_version

    async def check_capabilities(self, capabilities: str | list[str]) -> list[str]:
        """Returns the list with missing capabilities if any."""
        return check_capabilities(capabilities, await self.capabilities)

    async def update_server_info(self) -> None:
        """Updates the capabilities and the Nextcloud version.

        *In normal cases, it is called automatically and there is no need to call it manually.*
        """
        await self._session.update_server_info()

    @property
    def response_headers(self) -> Headers:
        """Returns the `HTTPX headers <https://www.python-httpx.org/api/#headers>`_ from the last response."""
        return self._session.response_headers

    @property
    async def theme(self) -> ThemingInfo | None:
        """Returns Theme information."""
        return get_parsed_theme((await self.capabilities)["theming"]) if "theming" in await self.capabilities else None

    async def ocs(
        self,
        method: str,
        path: str,
        *,
        content: bytes | str | typing.Iterable[bytes] | typing.AsyncIterable[bytes] | None = None,
        json: dict | list | None = None,
        params: dict | None = None,
        **kwargs,
    ):
        """Performs OCS call and returns OCS response payload data."""
        return await self._session.ocs(method, path, content=content, json=json, params=params, **kwargs)


class Nextcloud(_NextcloudBasic):
    """Nextcloud client class.

    Allows you to connect to Nextcloud and perform operations on files, shares, users, and everything else.
    """

    _session: NcSession

    def __init__(self, **kwargs):
        """If the parameters are not specified, they will be taken from the environment.

        :param nextcloud_url: url of the nextcloud instance.
        :param nc_auth_user: login username.
        :param nc_auth_pass: password or app-password for the username.
        """
        self._session = NcSession(**kwargs)
        super().__init__(self._session)

    @property
    def user(self) -> str:
        """Returns current user ID."""
        return self._session.user


class AsyncNextcloud(_AsyncNextcloudBasic):
    """Async Nextcloud client class.

    Allows you to connect to Nextcloud and perform operations on files, shares, users, and everything else.
    """

    _session: AsyncNcSession

    def __init__(self, **kwargs):
        """If the parameters are not specified, they will be taken from the environment.

        :param nextcloud_url: url of the nextcloud instance.
        :param nc_auth_user: login username.
        :param nc_auth_pass: password or app-password for the username.
        """
        self._session = AsyncNcSession(**kwargs)
        super().__init__(self._session)

    @property
    async def user(self) -> str:
        """Returns current user ID."""
        return await self._session.user


class NextcloudApp(_NextcloudBasic):
    """Class for communication with Nextcloud in Nextcloud applications.

    Provides additional API required for applications such as user impersonation,
    endpoint registration, new authentication method, etc.

    .. note:: Instance of this class should not be created directly in ``normal`` applications,
        it will be provided for each app endpoint call.
    """

    _session: NcSessionApp
    appconfig_ex: AppConfigExAPI
    """Nextcloud App Preferences API for ExApps"""
    preferences_ex: PreferencesExAPI
    """Nextcloud User Preferences API for ExApps"""
    ui: UiApi
    """Nextcloud UI API for ExApps"""

    def __init__(self, **kwargs):
        """The parameters will be taken from the environment.

        They can be overridden by specifying them in **kwargs**, but this behavior is highly discouraged.
        """
        self._session = NcSessionApp(**kwargs)
        super().__init__(self._session)
        self.appconfig_ex = AppConfigExAPI(self._session)
        self.preferences_ex = PreferencesExAPI(self._session)
        self.ui = UiApi(self._session)

    def log(self, log_lvl: LogLvl, content: str) -> None:
        """Writes log to the Nextcloud log file."""
        if self.check_capabilities("app_api"):
            return
        if int(log_lvl) < self.capabilities["app_api"].get("loglevel", 0):
            return
        self._session.ocs("POST", f"{self._session.ae_url}/log", json={"level": int(log_lvl), "message": content})

    def users_list(self) -> list[str]:
        """Returns list of users on the Nextcloud instance. **Available** only for ``System`` applications."""
        return self._session.ocs("GET", f"{self._session.ae_url}/users")

    def scope_allowed(self, scope: ApiScope) -> bool:
        """Check if API scope is avalaible for application.

        Useful for applications that declare optional scopes to check if they are allowed.
        """
        if self.check_capabilities("app_api"):
            return False
        return scope in self.capabilities["app_api"]["scopes"]

    @property
    def user(self) -> str:
        """Property containing the current user ID.

        **System Applications** can change user ID they impersonate with **set_user** method.
        """
        return self._session.user

    def set_user(self, user_id: str):
        """Changes current User ID."""
        if self._session.user != user_id:
            self._session.set_user(user_id)
            self.talk.config_sha = ""
            self.talk.modified_since = 0
            self.activity.last_given = 0
            self.notes.last_etag = ""
            self._session.update_server_info()

    @property
    def app_cfg(self) -> AppConfig:
        """Returns deploy config, with AppAPI version, Application version and name."""
        return self._session.cfg

    def register_talk_bot(self, callback_url: str, display_name: str, description: str = "") -> tuple[str, str]:
        """Registers Talk BOT.

        .. note:: AppAPI will add a record in a case of successful registration to the ``appconfig_ex`` table.

        :param callback_url: URL suffix for fetching new messages. MUST be ``UNIQ`` for each bot the app provides.
        :param display_name: The name under which the messages will be posted.
        :param description: Optional description shown in the admin settings.
        :return: Tuple with ID and the secret used for signing requests.
        """
        require_capabilities("app_api", self._session.capabilities)
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        params = {
            "name": display_name,
            "route": callback_url,
            "description": description,
        }
        result = self._session.ocs("POST", f"{self._session.ae_url}/talk_bot", json=params)
        return result["id"], result["secret"]

    def unregister_talk_bot(self, callback_url: str) -> bool:
        """Unregisters Talk BOT."""
        require_capabilities("app_api", self._session.capabilities)
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        params = {
            "route": callback_url,
        }
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/talk_bot", json=params)
        except NextcloudExceptionNotFound:
            return False
        return True

    def request_sign_check(self, request: FastAPIRequest) -> bool:
        """Verifies the signature and validity of an incoming request from the Nextcloud.

        :param request: The `Starlette request <https://www.starlette.io/requests/>`_

        .. note:: In most cases ``nc: Annotated[NextcloudApp, Depends(nc_app)]`` should be used.
        """
        try:
            self._session.sign_check(request)
        except ValueError as e:
            print(e)
            return False
        return True

    def set_init_status(self, progress: int, error: str = "") -> None:
        """Sets state of the app initialization.

        :param progress: a number from ``0`` to ``100`` indicating the percentage of application readiness for work.
            After sending ``100`` AppAPI will enable the application.
        :param error: if non-empty, signals to AppAPI that the application cannot be initialized successfully.
        """
        self._session.ocs(
            "PUT",
            f"/ocs/v1.php/apps/app_api/apps/status/{self._session.cfg.app_name}",
            json={
                "progress": progress,
                "error": error,
            },
        )


class AsyncNextcloudApp(_AsyncNextcloudBasic):
    """Class for communication with Nextcloud in Async Nextcloud applications.

    Provides additional API required for applications such as user impersonation,
    endpoint registration, new authentication method, etc.

    .. note:: Instance of this class should not be created directly in ``normal`` applications,
        it will be provided for each app endpoint call.
    """

    _session: AsyncNcSessionApp
    appconfig_ex: AsyncAppConfigExAPI
    """Nextcloud App Preferences API for ExApps"""
    preferences_ex: AsyncPreferencesExAPI
    """Nextcloud User Preferences API for ExApps"""
    ui: AsyncUiApi
    """Nextcloud UI API for ExApps"""

    def __init__(self, **kwargs):
        """The parameters will be taken from the environment.

        They can be overridden by specifying them in **kwargs**, but this behavior is highly discouraged.
        """
        self._session = AsyncNcSessionApp(**kwargs)
        super().__init__(self._session)
        self.appconfig_ex = AsyncAppConfigExAPI(self._session)
        self.preferences_ex = AsyncPreferencesExAPI(self._session)
        self.ui = AsyncUiApi(self._session)

    async def log(self, log_lvl: LogLvl, content: str) -> None:
        """Writes log to the Nextcloud log file."""
        if await self.check_capabilities("app_api"):
            return
        if int(log_lvl) < (await self.capabilities)["app_api"].get("loglevel", 0):
            return
        await self._session.ocs("POST", f"{self._session.ae_url}/log", json={"level": int(log_lvl), "message": content})

    async def users_list(self) -> list[str]:
        """Returns list of users on the Nextcloud instance. **Available** only for ``System`` applications."""
        return await self._session.ocs("GET", f"{self._session.ae_url}/users")

    async def scope_allowed(self, scope: ApiScope) -> bool:
        """Check if API scope is avalaible for application.

        Useful for applications that declare optional scopes to check if they are allowed.
        """
        if await self.check_capabilities("app_api"):
            return False
        return scope in (await self.capabilities)["app_api"]["scopes"]

    @property
    async def user(self) -> str:
        """Property containing the current user ID.

        **System Applications** can change user ID they impersonate with **set_user** method.
        """
        return await self._session.user

    async def set_user(self, user_id: str):
        """Changes current User ID."""
        if await self._session.user != user_id:
            self._session.set_user(user_id)
            self.talk.config_sha = ""
            self.talk.modified_since = 0
            self.activity.last_given = 0
            self.notes.last_etag = ""
            await self._session.update_server_info()

    @property
    def app_cfg(self) -> AppConfig:
        """Returns deploy config, with AppAPI version, Application version and name."""
        return self._session.cfg

    async def register_talk_bot(self, callback_url: str, display_name: str, description: str = "") -> tuple[str, str]:
        """Registers Talk BOT.

        .. note:: AppAPI will add a record in a case of successful registration to the ``appconfig_ex`` table.

        :param callback_url: URL suffix for fetching new messages. MUST be ``UNIQ`` for each bot the app provides.
        :param display_name: The name under which the messages will be posted.
        :param description: Optional description shown in the admin settings.
        :return: Tuple with ID and the secret used for signing requests.
        """
        require_capabilities("app_api", await self._session.capabilities)
        require_capabilities("spreed.features.bots-v1", await self._session.capabilities)
        params = {
            "name": display_name,
            "route": callback_url,
            "description": description,
        }
        result = await self._session.ocs("POST", f"{self._session.ae_url}/talk_bot", json=params)
        return result["id"], result["secret"]

    async def unregister_talk_bot(self, callback_url: str) -> bool:
        """Unregisters Talk BOT."""
        require_capabilities("app_api", await self._session.capabilities)
        require_capabilities("spreed.features.bots-v1", await self._session.capabilities)
        params = {
            "route": callback_url,
        }
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/talk_bot", json=params)
        except NextcloudExceptionNotFound:
            return False
        return True

    def request_sign_check(self, request: FastAPIRequest) -> bool:
        """Verifies the signature and validity of an incoming request from the Nextcloud.

        :param request: The `Starlette request <https://www.starlette.io/requests/>`_

        .. note:: In most cases ``nc: Annotated[NextcloudApp, Depends(nc_app)]`` should be used.
        """
        try:
            self._session.sign_check(request)
        except ValueError as e:
            print(e)
            return False
        return True

    async def set_init_status(self, progress: int, error: str = "") -> None:
        """Sets state of the app initialization.

        :param progress: a number from ``0`` to ``100`` indicating the percentage of application readiness for work.
            After sending ``100`` AppAPI will enable the application.
        :param error: if non-empty, signals to AppAPI that the application cannot be initialized successfully.
        """
        await self._session.ocs(
            "PUT",
            f"/ocs/v1.php/apps/app_api/apps/status/{self._session.cfg.app_name}",
            json={
                "progress": progress,
                "error": error,
            },
        )
