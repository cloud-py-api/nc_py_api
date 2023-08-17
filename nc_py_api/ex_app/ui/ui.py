"""Nextcloud API for User Interface."""

from dataclasses import dataclass

from ..._session import NcSessionApp
from .files import _UiFilesActionsAPI


@dataclass
class UiApi:
    """Class that encapsulates all UI functionality."""

    files_dropdown_menu: _UiFilesActionsAPI
    """File dropdown menu API."""

    def __init__(self, session: NcSessionApp):
        self.files_dropdown_menu = _UiFilesActionsAPI(session)
