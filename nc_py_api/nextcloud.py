"""
Nextcloud class providing access to all API endpoints.
"""
from abc import ABC
from typing import Optional, Union

from fastapi import Request

from ._session import AppConfig, NcSession, NcSessionApp, NcSessionBasic, ServerVersion
from .appconfig_preferences_ex import AppConfigExAPI, PreferencesExAPI
from .apps import AppAPI
from .constants import APP_V2_BASIC_URL, ApiScope, LogLvl
from .files import FilesAPI
from .files_sharing import FilesSharingAPI
from .misc import check_capabilities
from .preferences import PreferencesAPI
from .theming import ThemingInfo, get_parsed_theme
from .ui_files_actions_menu import UiFilesActionsAPI
from .users import UsersAPI
from .users_groups import UserGroupsAPI
from .users_status import UserStatusAPI
from .weather_status import WeatherStatusAPI


class NextcloudBasic(ABC):
    apps: AppAPI
    files: FilesAPI
    files_sharing: FilesSharingAPI
    preferences_api: PreferencesAPI
    users: UsersAPI
    users_groups: UserGroupsAPI
    users_status: UserStatusAPI
    weather_status: WeatherStatusAPI
    _session: NcSessionBasic

    def _init_api(self, session: NcSessionBasic):
        self.apps = AppAPI(session)
        self.files = FilesAPI(session)
        self.files_sharing = FilesSharingAPI(session)
        self.preferences_api = PreferencesAPI(session)
        self.users = UsersAPI(session)
        self.users_groups = UserGroupsAPI(session)
        self.users_status = UserStatusAPI(session)
        self.weather_status = WeatherStatusAPI(session)

    @property
    def capabilities(self) -> dict:
        return self._session.capabilities

    @property
    def srv_version(self) -> ServerVersion:
        return self._session.nc_version

    def check_capabilities(self, capabilities: Union[str, list[str]]) -> list[str]:
        return check_capabilities(capabilities, self.capabilities)

    def update_server_info(self) -> None:
        self._session.update_server_info()

    @property
    def theme(self) -> Optional[ThemingInfo]:
        return get_parsed_theme(self.capabilities["theming"]) if "theming" in self.capabilities else None


class Nextcloud(NextcloudBasic):
    _session: NcSession

    def __init__(self, **kwargs):
        self._session = NcSession(**kwargs)
        self._init_api(self._session)

    @property
    def user(self):
        return self._session.user


class NextcloudApp(NextcloudBasic):
    _session: NcSessionApp
    appconfig_ex_api: AppConfigExAPI
    preferences_ex_api: PreferencesExAPI
    ui_files_actions: UiFilesActionsAPI

    def __init__(self, **kwargs):
        self._session = NcSessionApp(**kwargs)
        self._init_api(self._session)
        self.appconfig_ex_api = AppConfigExAPI(self._session)
        self.preferences_ex_api = PreferencesExAPI(self._session)
        self.ui_files_actions = UiFilesActionsAPI(self._session)

    def log(self, log_lvl: LogLvl, content: str):
        if self.check_capabilities("app_ecosystem_v2"):
            return
        if int(log_lvl) < self.capabilities["app_ecosystem_v2"].get("loglevel", 0):
            return
        self._session.ocs(
            method="POST", path=f"{APP_V2_BASIC_URL}/log", json={"level": int(log_lvl), "message": content}
        )

    # def download_log(self) -> bytes:
    #     return self._session.ocs(method="GET", path=f"{APP_V2_BASIC_URL}/log")

    def users_list(self) -> list[str]:
        return self._session.ocs("GET", path=f"{APP_V2_BASIC_URL}/users", params={"format": "json"})

    def scope_allowed(self, scope: ApiScope) -> bool:
        if self.check_capabilities("app_ecosystem_v2"):
            return False
        return scope in self.capabilities["app_ecosystem_v2"]["scopes"]

    @property
    def user(self):
        return self._session.user

    @user.setter
    def user(self, value: str):
        if self._session.user != value:
            self._session.user = value
            self._session.update_server_info()

    @property
    def app_cfg(self) -> AppConfig:
        return self._session.cfg

    def request_sign_check(self, request: Request) -> bool:
        try:
            self._session.sign_check(request)
        except ValueError as e:
            print(e)
            return False
        return True
