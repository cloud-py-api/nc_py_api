"""Common constants. Do not use them directly, all public ones are imported from __init__.py."""

from enum import IntEnum
from typing import TypedDict


class LogLvl(IntEnum):
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


APP_V2_BASIC_URL = "/ocs/v1.php/apps/app_ecosystem_v2/api/v1"


class ApiScope(IntEnum):
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


class ApiScopesStruct(TypedDict):
    """Reply of the Nextcloud App with the desired scopes."""

    required: list[int]
    optional: list[int]


class OCSRespond(IntEnum):
    """Special Nextcloud respond statuses for OCS calls."""

    RESPOND_SERVER_ERROR = 996
    RESPOND_UNAUTHORISED = 997
    RESPOND_NOT_FOUND = 998
    RESPOND_UNKNOWN_ERROR = 999
