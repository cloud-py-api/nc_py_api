"""Definitions related to the Graphical User Interface."""
from pydantic import BaseModel


class GuiActionFileInfo(BaseModel):
    """File Information Nextcloud sends to the External Application."""

    fileId: int
    name: str
    directory: str
    etag: str
    mime: str
    favorite: str
    permissions: int


class GuiFileActionHandlerInfo(BaseModel):
    """Action information Nextcloud sends to the External Application."""

    actionName: str
    actionHandler: str
    actionFile: GuiActionFileInfo
