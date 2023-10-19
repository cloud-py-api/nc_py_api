"""Nextcloud class providing access to all API endpoints."""
from abc import ABC
from typing import Optional, Union

from fastapi import Request
from httpx import Headers as HttpxHeaders

from ._exceptions import NextcloudExceptionNotFound
from ._misc import check_capabilities, require_capabilities
from ._preferences import PreferencesAPI
from ._preferences_ex import AppConfigExAPI, PreferencesExAPI
from ._session import AppConfig, NcSession, NcSessionApp, NcSessionBasic, ServerVersion
from ._talk_api import _TalkAPI
from ._theming import ThemingInfo, get_parsed_theme
from .activity import _ActivityAPI
from .apps import _AppsAPI
from .calendar import _CalendarAPI
from .ex_app.defs import ApiScope, LogLvl
from .ex_app.ui.ui import UiApi
from .files.files import FilesAPI
from .notes import _NotesAPI
from .notifications import _NotificationsAPI
from .user_status import _UserStatusAPI
from .users import _UsersAPI
from .users_groups import _UsersGroupsAPI
from .weather_status import _WeatherStatusAPI


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
    """Nextcloud Talk Api"""
    users: _UsersAPI
    """Nextcloud API for managing users."""
    users_groups: _UsersGroupsAPI
    """Nextcloud API for managing user groups."""
    user_status: _UserStatusAPI
    """Nextcloud API for managing users statuses"""
    weather_status: _WeatherStatusAPI
    """Nextcloud API for managing user weather statuses"""
    _session: NcSessionBasic

    def _init_api(self, session: NcSessionBasic):
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

    def check_capabilities(self, capabilities: Union[str, list[str]]) -> list[str]:
        """Returns the list with missing capabilities if any.

        :param capabilities: one or more features to check for.
        """
        return check_capabilities(capabilities, self.capabilities)

    def update_server_info(self) -> None:
        """Updates the capabilities and the Nextcloud version.

        *In normal cases, it is called automatically and there is no need to call it manually.*
        """
        self._session.update_server_info()

    @property
    def response_headers(self) -> HttpxHeaders:
        """Returns the `HTTPX headers <https://www.python-httpx.org/api/#headers>`_ from the last response."""
        return self._session.response_headers

    @property
    def theme(self) -> Optional[ThemingInfo]:
        """Returns Theme information."""
        return get_parsed_theme(self.capabilities["theming"]) if "theming" in self.capabilities else None


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
        self._init_api(self._session)

    @property
    def user(self) -> str:
        """Returns current user ID."""
        return self._session.user


class NextcloudApp(_NextcloudBasic):
    """Class for creating Nextcloud applications.

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
        self._init_api(self._session)
        self.appconfig_ex = AppConfigExAPI(self._session)
        self.preferences_ex = PreferencesExAPI(self._session)
        self.ui = UiApi(self._session)

    def log(self, log_lvl: LogLvl, content: str) -> None:
        """Writes log to the Nextcloud log file.

        :param log_lvl: level of the log, content belongs to.
        :param content: string to write into the log.
        """
        if self.check_capabilities("app_api"):
            return
        if int(log_lvl) < self.capabilities["app_api"].get("loglevel", 0):
            return
        self._session.ocs(
            method="POST", path=f"{self._session.ae_url}/log", json={"level": int(log_lvl), "message": content}
        )

    def users_list(self) -> list[str]:
        """Returns list of users on the Nextcloud instance. **Available** only for ``System`` applications."""
        return self._session.ocs("GET", path=f"{self._session.ae_url}/users", params={"format": "json"})

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

        *System Applications* can set it and impersonate the user. For normal applications, it is set automatically.
        """
        return self._session.user

    @user.setter
    def user(self, value: str):
        if self._session.user != value:
            self._session.user = value
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
        :return: The secret used for signing requests.
        """
        require_capabilities("app_api", self._session.capabilities)
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        params = {
            "name": display_name,
            "route": callback_url,
            "description": description,
        }
        result = self._session.ocs(method="POST", path=f"{self._session.ae_url}/talk_bot", json=params)
        return result["id"], result["secret"]

    def unregister_talk_bot(self, callback_url: str) -> bool:
        """Unregisters Talk BOT.

        :param callback_url: URL suffix for fetching new messages. MUST be ``UNIQ`` for each bot the app provides.
        :return: The secret used for signing requests.
        """
        require_capabilities("app_api", self._session.capabilities)
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        params = {
            "route": callback_url,
        }
        try:
            self._session.ocs(method="DELETE", path=f"{self._session.ae_url}/talk_bot", json=params)
        except NextcloudExceptionNotFound:
            return False
        return True

    def request_sign_check(self, request: Request) -> bool:
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
            method="PUT",
            path=f"/ocs/v1.php/apps/app_api/apps/status/{self._session.cfg.app_name}",
            json={
                "progress": progress,
                "error": error,
            },
            not_parse=True,
        )
