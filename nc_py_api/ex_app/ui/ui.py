"""Nextcloud API for User Interface."""

from ..._session import AsyncNcSessionApp, NcSessionApp
from .files_actions import _AsyncUiFilesActionsAPI, _UiFilesActionsAPI
from .resources import _AsyncUiResources, _UiResources
from .settings import _AsyncDeclarativeSettingsAPI, _DeclarativeSettingsAPI
from .top_menu import _AsyncUiTopMenuAPI, _UiTopMenuAPI


class UiApi:
    """Class that encapsulates all UI functionality."""

    files_dropdown_menu: _UiFilesActionsAPI
    """File dropdown menu API."""
    top_menu: _UiTopMenuAPI
    """Top App menu API."""
    resources: _UiResources
    """Page(Template) resources API."""
    settings: _DeclarativeSettingsAPI
    """API for ExApp settings UI"""

    def __init__(self, session: NcSessionApp):
        self.files_dropdown_menu = _UiFilesActionsAPI(session)
        self.top_menu = _UiTopMenuAPI(session)
        self.resources = _UiResources(session)
        self.settings = _DeclarativeSettingsAPI(session)


class AsyncUiApi:
    """Class that encapsulates all UI functionality(async)."""

    files_dropdown_menu: _AsyncUiFilesActionsAPI
    """File dropdown menu API."""
    top_menu: _AsyncUiTopMenuAPI
    """Top App menu API."""
    resources: _AsyncUiResources
    """Page(Template) resources API."""
    settings: _AsyncDeclarativeSettingsAPI
    """API for ExApp settings UI"""

    def __init__(self, session: AsyncNcSessionApp):
        self.files_dropdown_menu = _AsyncUiFilesActionsAPI(session)
        self.top_menu = _AsyncUiTopMenuAPI(session)
        self.resources = _AsyncUiResources(session)
        self.settings = _AsyncDeclarativeSettingsAPI(session)
