"""Nextcloud API for User Interface."""

from dataclasses import dataclass

from ._session import NcSessionApp
from .gui_files import GuiFilesActionsAPI


@dataclass
class GuiApi:
    """Class that encapsulates all UI functionality."""

    files_dropdown_menu: GuiFilesActionsAPI

    def __init__(self, session: NcSessionApp):
        self.files_dropdown_menu = GuiFilesActionsAPI(session)
