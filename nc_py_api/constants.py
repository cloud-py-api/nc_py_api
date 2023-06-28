"""Common constants. Do not use them directly, all public ones are imported to __init__.py"""

from enum import IntEnum
from typing import TypedDict


class LogLvl(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    FATAL = 4


APP_V2_BASIC_URL = "/ocs/v2.php/apps/app_ecosystem_v2/api/v1"


class ApiScope(IntEnum):
    SYSTEM = 2
    DAV = 3
    USER_INFO = 10
    USER_STATUS = 11
    NOTIFICATIONS = 12


class ApiScopesStruct(TypedDict):
    required: list[int]
    optional: list[int]
