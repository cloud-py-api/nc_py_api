"""Transparent logging support to store logs in the nextcloud.log."""

import asyncio
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
    """Forwards Python ``logging`` records to ``nextcloud.log`` via :py:meth:`NextcloudApp.log`.

    Python's logging API is synchronous but ``NextcloudApp.log`` is a coroutine, so each
    record is dispatched to a captured event loop with :func:`asyncio.run_coroutine_threadsafe`.
    The dispatch is fire-and-forget so emitters never block. If no loop was captured (for
    example, ``setup_nextcloud_logging`` was called outside of a running loop), records are
    silently dropped to avoid deadlocking caller threads.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None):
        super().__init__()
        self._loop = loop

    def emit(self, record):
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        if THREAD_LOCAL.__dict__.get("nc_py_api.loghandler", False):
            return

        try:
            THREAD_LOCAL.__dict__["nc_py_api.loghandler"] = True
            log_entry = self.format(record)
            log_level = record.levelno
            asyncio.run_coroutine_threadsafe(
                NextcloudApp().log(LOGLVL_MAP.get(log_level, LogLvl.FATAL), log_entry, fast_send=True),
                loop,
            )
        except Exception:  # noqa pylint: disable=broad-exception-caught
            self.handleError(record)
        finally:
            THREAD_LOCAL.__dict__["nc_py_api.loghandler"] = False


def setup_nextcloud_logging(logger_name: str | None = None, logging_level: int = logging.DEBUG):
    """Attach a handler that streams Python logging records to the Nextcloud log file.

    Must be called from a context with a running asyncio event loop (typically your
    FastAPI ``lifespan`` or any async startup hook). The captured loop is used to
    schedule the async :py:meth:`NextcloudApp.log` calls from sync ``emit``. Calling
    this from sync code installs an inert handler that drops records.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    logger = logging.getLogger(logger_name)
    nextcloud_handler = _NextcloudLogsHandler(loop)
    nextcloud_handler.setLevel(logging_level)
    logger.addHandler(nextcloud_handler)
    return nextcloud_handler
