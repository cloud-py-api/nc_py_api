"""Additional definitions for NextcloudApp."""

import enum


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


class ApiScope(enum.IntEnum):
    """Default API scopes. Should be used as a parameter to the :py:meth:`~.NextcloudApp.scope_allowed` method."""

    SYSTEM = 2
    """Allows access to the System APIs."""
    FILES = 10
    """Allows access to the Nextcloud file base."""
    FILES_SHARING = 11
    """Allows access to APIs that provide File Sharing."""
    USER_INFO = 30
    """Allows access to APIs that work with users."""
    USER_STATUS = 31
    """Allows access to APIs that work with users statuses."""
    NOTIFICATIONS = 32
    """Allows access to APIs that provide Notifications."""
    WEATHER_STATUS = 33
    """Allows access to APIs that provide Weather status."""
    TALK = 50
    """Allows access to Talk API endpoints."""
    TALK_BOT = 60
    """Allows to register Talk Bots."""
    ACTIVITIES = 110
    """Activity App endpoints."""
    NOTES = 120
    """Notes App endpoints"""
