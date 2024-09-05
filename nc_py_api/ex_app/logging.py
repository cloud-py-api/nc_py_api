"""Transparent logging support to store logs in the nextcloud.log."""

import logging
import threading

from ..nextcloud import NextcloudApp
from .defs import LogLvl

LOGLVL_MAP = {
    logging.NOTSET: LogLvl.DEBUG,
    logging.DEBUG: LogLvl.DEBUG,
    logging.INFO: LogLvl.INFO,
    logging.WARNING: LogLvl.WARNING,
    logging.ERROR: LogLvl.ERROR,
    logging.CRITICAL: LogLvl.FATAL,
}

THREAD_LOCAL = threading.local()


class _NextcloudLogsHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        if THREAD_LOCAL.__dict__.get("nc_py_api.loghandler", False):
            return

        try:
            THREAD_LOCAL.__dict__["nc_py_api.loghandler"] = True
            log_entry = self.format(record)
            log_level = record.levelno
            NextcloudApp().log(LOGLVL_MAP.get(log_level, LogLvl.FATAL), log_entry, fast_send=True)
        except Exception:  # noqa pylint: disable=broad-exception-caught
            self.handleError(record)
        finally:
            THREAD_LOCAL.__dict__["nc_py_api.loghandler"] = False


def setup_nextcloud_logging(logger_name: str | None = None, logging_level: int = logging.DEBUG):
    """Function to easily send all or selected log entries to Nextcloud."""
    logger = logging.getLogger(logger_name)
    nextcloud_handler = _NextcloudLogsHandler()
    nextcloud_handler.setLevel(logging_level)
    logger.addHandler(nextcloud_handler)
    return nextcloud_handler
