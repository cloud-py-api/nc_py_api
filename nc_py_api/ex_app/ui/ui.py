"""Nextcloud API for User Interface."""

from dataclasses import dataclass

from ..._session import NcSessionApp
from .files_actions import _UiFilesActionsAPI
from .resources import _UiResources
from .top_menu import _UiTopMenuAPI


@dataclass
class UiApi:
    """Class that encapsulates all UI functionality."""

    files_dropdown_menu: _UiFilesActionsAPI
    """File dropdown menu API."""
    top_menu: _UiTopMenuAPI
    """Top App menu API."""
    resources: _UiResources
    """Page(Template) resources API."""

    def __init__(self, session: NcSessionApp):
        self.files_dropdown_menu = _UiFilesActionsAPI(session)
        self.top_menu = _UiTopMenuAPI(session)
        self.resources = _UiResources(session)
