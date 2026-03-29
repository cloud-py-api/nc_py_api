"""Nextcloud API for User Interface."""

from ..._session import AsyncNcSessionApp
from .files_actions import _UiFilesActionsAPI
from .resources import _UiResources
from .settings import _DeclarativeSettingsAPI
from .top_menu import _UiTopMenuAPI


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

    def __init__(self, session: AsyncNcSessionApp):
        self.files_dropdown_menu = _UiFilesActionsAPI(session)
        self.top_menu = _UiTopMenuAPI(session)
        self.resources = _UiResources(session)
        self.settings = _DeclarativeSettingsAPI(session)
