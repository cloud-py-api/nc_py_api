"""Transparent logging support to store logs in the nextcloud.log."""

import logging

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


class _NextcloudStorageHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lock_flag = False

    def emit(self, record):
        if self.lock_flag:
            return

        try:
            self.lock_flag = True
            log_entry = self.format(record)
            log_level = record.levelno
            NextcloudApp().log(_python_loglvl_to_nextcloud(log_level), log_entry, fast_send=True)
        except Exception:  # noqa pylint: disable=broad-exception-caught
            self.handleError(record)
        finally:
            self.lock_flag = False


def setup_nextcloud_logging(logger_name: str | None = None, logging_level: int = logging.DEBUG):
    """Function to easily send all or selected log entries to Nextcloud."""
    logger = logging.getLogger(logger_name)
    nextcloud_handler = _NextcloudStorageHandler()
    nextcloud_handler.setLevel(logging_level)
    logger.addHandler(nextcloud_handler)
    return nextcloud_handler
