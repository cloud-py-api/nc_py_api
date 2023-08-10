"""Additional definitions for NextcloudApp."""

import enum
import typing


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
    """Default API scopes."""

    SYSTEM = 2
    """Allows access to the System APIs."""
    DAV = 3
    """Allows access to the Nextcloud file base."""
    USER_INFO = 10
    """Allows access to APIs that work with users."""
    USER_STATUS = 11
    """Allows access to APIs that work with users statuses."""
    NOTIFICATIONS = 12
    """Allows access to APIs that provide Notifications."""
    WEATHER_STATUS = 13
    """Allows access to APIs that provide Weather status."""
    FILES_SHARING = 14
    """Allows access to APIs that provide File Sharing."""


class ApiScopesStruct(typing.TypedDict):
    """Reply of the Nextcloud App with the desired scopes."""

    required: list[int]
    optional: list[int]
