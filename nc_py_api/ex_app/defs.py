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
