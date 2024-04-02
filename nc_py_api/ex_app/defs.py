"""Additional definitions for NextcloudApp."""

import enum

from pydantic import BaseModel

from ..files import ActionFileInfo


class LogLvl(enum.IntEnum):
    """Log levels."""

    DEBUG = 0
    """Debug log level"""
    INFO = 1
    """Informational log level"""
    WARNING = 2
    """Warning log level. ``Default``"""
    ERROR = 3
    """Error log level"""
    FATAL = 4
    """Fatal log level"""


class FileSystemEventData(BaseModel):
    """FileSystem events format."""

    target: ActionFileInfo
    source: ActionFileInfo | None = None


class FileSystemEventNotification(BaseModel):
    """AppAPI event notification common data."""

    event_type: str
    event_subtype: str
    event_data: FileSystemEventData
