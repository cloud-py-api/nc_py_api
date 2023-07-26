"""Common constants. Do not use them directly, all public ones are imported to __init__.py"""

from enum import IntEnum, IntFlag
from typing import TypedDict


class LogLvl(IntEnum):
    """Log levels"""

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
    """Default API scopes"""

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
    required: list[int]
    optional: list[int]


class OCSRespond(IntEnum):
    RESPOND_SERVER_ERROR = 996
    RESPOND_UNAUTHORISED = 997
    RESPOND_NOT_FOUND = 998
    RESPOND_UNKNOWN_ERROR = 999


class SharePermissions(IntFlag):
    """The share permissions to be set"""

    PERMISSION_READ = 1
    """Access to read"""
    PERMISSION_UPDATE = 2
    """Access to write"""
    PERMISSION_CREATE = 4
    """Access to create new objects in the share"""
    PERMISSION_DELETE = 8
    """Access to remove objects in the share"""
    PERMISSION_SHARE = 16
    """Access to re-share objects in the share"""


class ShareType(IntEnum):
    """Type of the object that will receive share"""

    TYPE_USER = 0
    """Share to the user"""
    TYPE_GROUP = 1
    """Share to the group"""
    TYPE_LINK = 3
    """Share by link"""
    TYPE_EMAIL = 4
    """Share by the email"""
    TYPE_REMOTE = 6
    """Share to the Federation"""
    TYPE_CIRCLE = 7
    """Share to the Nextcloud Circle"""
    TYPE_GUEST = 8
    """Share to `Guest`"""
    TYPE_REMOTE_GROUP = 9
    """Share to the Federation group"""
    TYPE_ROOM = 10
    """Share to the Talk room"""
    TYPE_DECK = 11
    """Share to the Nextcloud Deck"""
    TYPE_SCIENCE_MESH = 15
    """Share to the Reva instance(Science Mesh)"""


class ShareStatus(IntEnum):
    """Status of the share"""

    STATUS_PENDING = 0
    """The share waits for acceptance"""
    STATUS_ACCEPTED = 1
    """The share was for accepted"""
    STATUS_REJECTED = 2
    """The share was for rejected"""
