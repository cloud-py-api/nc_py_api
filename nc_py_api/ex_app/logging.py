"""Transparent logging support to store logs in the nextcloud.log."""

import logging
import threading

from ..nextcloud import NextcloudApp
from .defs import LogLvl


def _python_loglvl_to_nextcloud(levelno: int) -> LogLvl:
    if levelno in (logging.NOTSET, logging.DEBUG):
        return LogLvl.DEBUG
    if levelno == logging.INFO:
        return LogLvl.INFO
    if levelno == logging.WARNING:
        return LogLvl.WARNING
    if levelno == logging.ERROR:
        return LogLvl.ERROR
    return LogLvl.FATAL


class _NextcloudLogsHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        if threading.local().__dict__.get("nc_py_api.loghandler", False):
            return

        try:
            threading.local().__dict__["nc_py_api.loghandler"] = True
            log_entry = self.format(record)
            log_level = record.levelno
            NextcloudApp().log(_python_loglvl_to_nextcloud(log_level), log_entry, fast_send=True)
        except Exception:  # noqa pylint: disable=broad-exception-caught
            self.handleError(record)
        finally:
            threading.local().__dict__["nc_py_api.loghandler"] = False


def setup_nextcloud_logging(logger_name: str | None = None, logging_level: int = logging.DEBUG):
    """Function to easily send all or selected log entries to Nextcloud."""
    logger = logging.getLogger(logger_name)
    nextcloud_handler = _NextcloudLogsHandler()
    nextcloud_handler.setLevel(logging_level)
    logger.addHandler(nextcloud_handler)
    return nextcloud_handler
