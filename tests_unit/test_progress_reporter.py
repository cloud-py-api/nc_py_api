"""Unit tests for the sync->async bridges added in Phase 2.

Cover the branches the integration tests can't reach: invocation without a
running loop, scheduling failures on the captured loop, and the logging
handler's loop-capture / disabled paths.
"""

import asyncio
import logging
import warnings
from unittest import mock

import pytest


def _async_mock(return_value=None):
    """Return a mock whose call result is an awaitable (coroutine)."""

    async def _coro(*args, **kwargs):
        return return_value

    return mock.MagicMock(side_effect=_coro)


class TestProgressReporter:
    def test_calls_set_init_status_with_progress_only_when_no_error(self):
        from nc_py_api.ex_app.integration_fastapi import _ProgressReporter

        nc = mock.MagicMock()
        reporter = _ProgressReporter(nc, loop=None)
        reporter(42)
        assert nc.set_init_status.call_args_list == [mock.call(42)]

    def test_passes_error_when_present(self):
        from nc_py_api.ex_app.integration_fastapi import _ProgressReporter

        nc = mock.MagicMock()
        reporter = _ProgressReporter(nc, loop=None)
        reporter(50, "boom")
        assert nc.set_init_status.call_args_list == [mock.call(50, "boom")]

    def test_closes_orphan_coroutine_when_loop_unavailable(self):
        from nc_py_api.ex_app.integration_fastapi import _ProgressReporter

        nc = mock.MagicMock()
        nc.set_init_status = _async_mock()
        reporter = _ProgressReporter(nc, loop=None)
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # promote "coroutine never awaited" to error
            reporter(75)
        nc.set_init_status.assert_called_once()

    def test_closes_orphan_coroutine_when_loop_closed(self):
        from nc_py_api.ex_app.integration_fastapi import _ProgressReporter

        loop = asyncio.new_event_loop()
        loop.close()
        nc = mock.MagicMock()
        nc.set_init_status = _async_mock()
        reporter = _ProgressReporter(nc, loop=loop)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            reporter(80)

    def test_schedules_on_running_loop_and_waits_for_result(self):
        from nc_py_api.ex_app.integration_fastapi import _ProgressReporter

        seen = []

        async def fake_set_init_status(progress, error=""):
            seen.append((progress, error))

        nc = mock.MagicMock()
        nc.set_init_status = fake_set_init_status

        async def driver():
            loop = asyncio.get_running_loop()
            reporter = _ProgressReporter(nc, loop)
            await asyncio.to_thread(reporter, 33)
            await asyncio.to_thread(reporter, 66, "warn")

        asyncio.run(driver())
        assert seen == [(33, ""), (66, "warn")]

    def test_swallows_scheduling_errors(self):
        from nc_py_api.ex_app.integration_fastapi import _ProgressReporter

        async def boom(*_args, **_kw):
            raise RuntimeError("nope")

        nc = mock.MagicMock()
        nc.set_init_status = boom

        async def driver():
            loop = asyncio.get_running_loop()
            reporter = _ProgressReporter(nc, loop)
            await asyncio.to_thread(reporter, 90)  # must not propagate the RuntimeError

        asyncio.run(driver())


class TestNextcloudLogsHandler:
    def test_emit_is_noop_without_captured_loop(self):
        from nc_py_api.ex_app.logger import _NextcloudLogsHandler

        handler = _NextcloudLogsHandler(loop=None)
        record = logging.LogRecord("name", logging.INFO, "p", 1, "msg", None, None)
        with mock.patch("nc_py_api.ex_app.logger.NextcloudApp") as nc_app_cls:
            handler.emit(record)
            nc_app_cls.assert_not_called()

    def test_emit_is_noop_when_loop_closed(self):
        from nc_py_api.ex_app.logger import _NextcloudLogsHandler

        loop = asyncio.new_event_loop()
        loop.close()
        handler = _NextcloudLogsHandler(loop=loop)
        record = logging.LogRecord("name", logging.INFO, "p", 1, "msg", None, None)
        with mock.patch("nc_py_api.ex_app.logger.NextcloudApp") as nc_app_cls:
            handler.emit(record)
            nc_app_cls.assert_not_called()

    def test_emit_dispatches_to_loop(self):
        from nc_py_api.ex_app.logger import LogLvl, _NextcloudLogsHandler

        seen: list[tuple] = []

        async def fake_log(level, message, fast_send=False):
            seen.append((int(level), message, fast_send))

        nc_instance = mock.MagicMock()
        nc_instance.log = fake_log

        async def driver():
            loop = asyncio.get_running_loop()
            handler = _NextcloudLogsHandler(loop=loop)
            handler.setFormatter(logging.Formatter("%(message)s"))
            record = logging.LogRecord("name", logging.WARNING, "p", 1, "hello", None, None)
            with mock.patch("nc_py_api.ex_app.logger.NextcloudApp", return_value=nc_instance):
                await asyncio.to_thread(handler.emit, record)
                # Yield to let the scheduled coroutine run.
                for _ in range(10):
                    if seen:
                        break
                    await asyncio.sleep(0.01)

        asyncio.run(driver())
        assert seen == [(int(LogLvl.WARNING), "hello", True)]


class TestSetupNextcloudLogging:
    def test_returns_inert_handler_outside_running_loop(self):
        from nc_py_api.ex_app.logger import (
            _NextcloudLogsHandler,
            setup_nextcloud_logging,
        )

        logger = logging.getLogger("nc_py_api_test_inert")
        logger.handlers.clear()
        try:
            handler = setup_nextcloud_logging("nc_py_api_test_inert")
            assert isinstance(handler, _NextcloudLogsHandler)
            assert handler._loop is None  # noqa: SLF001  - intentional
            assert handler in logger.handlers
        finally:
            logger.handlers.clear()

    def test_captures_running_loop(self):
        from nc_py_api.ex_app.logger import setup_nextcloud_logging

        async def driver():
            logger = logging.getLogger("nc_py_api_test_loop")
            logger.handlers.clear()
            try:
                handler = setup_nextcloud_logging("nc_py_api_test_loop")
                assert handler._loop is asyncio.get_running_loop()  # noqa: SLF001
            finally:
                logger.handlers.clear()

        asyncio.run(driver())


class TestFetchModelsTaskLoopParam:
    def test_passes_loop_to_progress_reporter(self):
        """``loop`` defaults to None outside an async context but can be provided."""
        from nc_py_api.ex_app.integration_fastapi import fetch_models_task

        nc = mock.MagicMock()
        # No models -> only the terminal ``set_init_status(100)`` should fire.
        fetch_models_task(nc, {}, 0)
        assert nc.set_init_status.call_args_list == [mock.call(100)]

    def test_uses_explicit_loop_when_provided(self):
        from nc_py_api.ex_app.integration_fastapi import fetch_models_task

        loop = asyncio.new_event_loop()
        try:
            nc = mock.MagicMock()
            fetch_models_task(nc, {}, 50, loop)
            assert nc.set_init_status.called
        finally:
            loop.close()


@pytest.mark.asyncio
async def test_fetch_models_task_inside_loop_picks_up_current():
    """When called from an async context with no explicit loop, ``fetch_models_task``
    auto-detects the running loop."""
    from nc_py_api.ex_app.integration_fastapi import fetch_models_task

    nc = mock.MagicMock()
    await asyncio.to_thread(fetch_models_task, nc, {}, 0)
    assert nc.set_init_status.called
