"""Tests for model file download with FileLock and atomic rename."""

import hashlib
import os
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from threading import Thread
from unittest import mock

import pytest
from filelock import FileLock
from filelock import Timeout as FileLockTimeout

from nc_py_api._exceptions import ModelFetchError
from nc_py_api.ex_app.integration_fastapi import (
    MODEL_FETCH_MAX_DELAY,
    fetch_models_task,
)


class FakeResponse:
    """Mock HTTP response for niquests.get() with streaming support."""

    def __init__(self, content: bytes, etag: str = "", status_code: int = 200, ok: bool = True):
        self.content = content
        self.status_code = status_code
        self.ok = ok
        self.text = "" if ok else "Not Found"
        self.history = []
        sha = hashlib.sha256(content).hexdigest()
        self.headers = {
            "Content-Length": str(len(content)),
            "ETag": etag or f'"{sha}"',
        }
        self.closed = 0

    def iter_raw(self, _chunk_size):
        yield self.content

    def close(self):
        self.closed += 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _mock_nc():
    nc = mock.MagicMock()
    nc.set_init_status = mock.MagicMock()
    return nc


class TestFetchModelAsFile:
    """Tests for __fetch_model_as_file via fetch_models_task."""

    def test_download_creates_file(self, tmp_path):
        content = b"model-data-abc"
        save_path = str(tmp_path / "model.bin")

        with mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=FakeResponse(content)):
            fetch_models_task(_mock_nc(), {"https://example.com/model.bin": {"save_path": save_path}}, 0)

        assert os.path.isfile(save_path)
        with open(save_path, "rb") as f:
            assert f.read() == content

    def test_no_tmp_file_remains_after_success(self, tmp_path):
        save_path = str(tmp_path / "model.bin")

        with mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=FakeResponse(b"data")):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        assert not os.path.exists(save_path + ".tmp")

    def test_lock_file_released_after_download(self, tmp_path):
        save_path = str(tmp_path / "model.bin")

        with mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=FakeResponse(b"data")):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        lock_path = save_path + ".lock"
        # Lock file may or may not exist (FileLock implementation detail),
        # but it must not be held — acquiring it should succeed immediately.
        lock = FileLock(lock_path, timeout=1)
        lock.acquire()
        lock.release()

    def test_skips_download_when_file_matches_etag(self, tmp_path):
        content = b"existing-model-data"
        sha = hashlib.sha256(content).hexdigest()
        etag = f'"{sha}"'
        save_path = str(tmp_path / "model.bin")
        with open(save_path, "wb") as f:
            f.write(content)

        call_count = {"iter_raw": 0}
        original_iter_raw = FakeResponse.iter_raw

        def tracking_iter_raw(self, chunk_size):
            call_count["iter_raw"] += 1
            yield from original_iter_raw(self, chunk_size)

        resp = FakeResponse(content, etag=etag)
        resp.iter_raw = lambda cs: tracking_iter_raw(resp, cs)

        with mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=resp):
            fetch_models_task(_mock_nc(), {"https://example.com/model.bin": {"save_path": save_path}}, 0)

        assert call_count["iter_raw"] == 0
        with open(save_path, "rb") as f:
            assert f.read() == content

    def test_tmp_file_cleaned_up_on_download_error(self, tmp_path):
        save_path = str(tmp_path / "model.bin")

        def failing_iter_raw(_chunk_size):
            yield b"partial"
            raise ConnectionError("network down")

        resp = FakeResponse(b"full-content")
        resp.iter_raw = failing_iter_raw

        with (
            mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=resp),
            pytest.raises(ModelFetchError),
        ):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        assert not os.path.exists(save_path + ".tmp")
        assert not os.path.exists(save_path)

    def test_original_file_untouched_on_download_error(self, tmp_path):
        save_path = str(tmp_path / "model.bin")
        with open(save_path, "wb") as f:
            f.write(b"original-good-data")

        def failing_iter_raw(_chunk_size):
            yield b"partial"
            raise ConnectionError("network down")

        resp = FakeResponse(b"new-content", etag='"different-etag"')
        resp.iter_raw = failing_iter_raw

        with (
            mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=resp),
            pytest.raises(ModelFetchError),
        ):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        with open(save_path, "rb") as f:
            assert f.read() == b"original-good-data"

    def test_http_error_raises_model_fetch_error(self, tmp_path):
        save_path = str(tmp_path / "model.bin")
        resp = FakeResponse(b"", status_code=404, ok=False)

        with (
            mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=resp),
            pytest.raises(ModelFetchError),
        ):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path}}, 0)

    def test_concurrent_downloads_do_not_corrupt(self, tmp_path):
        save_path = str(tmp_path / "model.bin")
        errors = []

        def download():
            try:
                fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path}}, 0)
            except Exception as e:  # noqa pylint: disable=broad-exception-caught
                errors.append(e)

        # Patch once around both threads to avoid mock.patch context manager
        # race: independent per-thread patches can restore the original
        # function while the other thread still needs the mock.
        responses = iter([FakeResponse(b"A" * 10000), FakeResponse(b"B" * 10000)])

        def mock_get(_url, **_kwargs):
            return next(responses)

        with mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", side_effect=mock_get):
            t1 = Thread(target=download)
            t2 = Thread(target=download)
            t1.start()
            t2.start()
            t1.join(timeout=60)
            t2.join(timeout=60)

        assert not errors, f"Threads raised errors: {errors}"
        assert os.path.isfile(save_path)
        with open(save_path, "rb") as f:
            data = f.read()
        # File must be entirely one content or the other — never mixed
        assert data in (b"A" * 10000, b"B" * 10000)

    def test_filelock_timeout_raises_model_fetch_error(self, tmp_path):
        save_path = str(tmp_path / "model.bin")
        lock = FileLock(save_path + ".lock")
        nc = _mock_nc()

        with (
            mock.patch("nc_py_api.ex_app.integration_fastapi.FileLock", side_effect=FileLockTimeout(lock)),
            pytest.raises(ModelFetchError),
        ):
            fetch_models_task(nc, {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        status_msg = nc.set_init_status.call_args_list[-1][0][1]
        assert "Timed out waiting for lock" in status_msg

    def test_progress_updates_sent(self, tmp_path):
        save_path = str(tmp_path / "model.bin")
        nc = _mock_nc()

        with mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=FakeResponse(b"data")):
            fetch_models_task(nc, {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        # set_init_status should be called at least for completion (100)
        assert nc.set_init_status.called
        # Last call should be 100 (completion)
        assert nc.set_init_status.call_args_list[-1] == mock.call(100)


def _throttled(status_code: int = 429, retry_after: str = "") -> FakeResponse:
    response = FakeResponse(b"", status_code=status_code, ok=False)
    if retry_after:
        response.headers["Retry-After"] = retry_after
    return response


def _serving(*responses):
    """Serves the given responses to `niquests.get`, one per call."""
    it = iter(responses)
    return mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", side_effect=lambda *_a, **_kw: next(it))


class TestFetchModelRetries:
    """Model hosters answer 429 when they throttle; the download has to survive that."""

    def test_retries_until_the_download_succeeds(self, tmp_path):
        save_path = str(tmp_path / "model.bin")
        content = b"model-data"
        throttled = (_throttled(429), _throttled(503))

        with (
            _serving(*throttled, FakeResponse(content)) as mocked,
            mock.patch("nc_py_api.ex_app.integration_fastapi.time.sleep") as sleep,
        ):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        assert mocked.call_count == 3
        assert sleep.call_count == 2
        # the body of a throttled answer is never read, so its connection has to be released explicitly
        assert [response.closed for response in throttled] == [1, 1]
        with open(save_path, "rb") as f:
            assert f.read() == content

    def test_gives_up_after_max_retries(self, tmp_path):
        save_path = str(tmp_path / "model.bin")

        with (
            _serving(*[_throttled() for _ in range(10)]) as mocked,
            mock.patch("nc_py_api.ex_app.integration_fastapi.time.sleep"),
            pytest.raises(ModelFetchError),
        ):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path, "max_retries": 3}}, 0)

        assert mocked.call_count == 4  # the first attempt plus `max_retries`

    def test_max_retries_zero_fails_on_the_first_answer(self, tmp_path):
        save_path = str(tmp_path / "model.bin")

        with (
            _serving(_throttled()) as mocked,
            mock.patch("nc_py_api.ex_app.integration_fastapi.time.sleep") as sleep,
            pytest.raises(ModelFetchError),
        ):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path, "max_retries": 0}}, 0)

        assert mocked.call_count == 1
        assert not sleep.called

    def test_does_not_retry_statuses_that_will_not_change(self, tmp_path):
        save_path = str(tmp_path / "model.bin")

        with (
            _serving(_throttled(404)) as mocked,
            mock.patch("nc_py_api.ex_app.integration_fastapi.time.sleep") as sleep,
            pytest.raises(ModelFetchError),
        ):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        assert mocked.call_count == 1
        assert not sleep.called


class TestRetryDelays:
    """`Retry-After` is followed when usable, but never long enough to hang an ExApp init."""

    @staticmethod
    def _waited(tmp_path, *responses) -> list[float]:
        with (
            _serving(*responses, FakeResponse(b"data")),
            mock.patch("nc_py_api.ex_app.integration_fastapi.time.sleep") as sleep,
        ):
            fetch_models_task(_mock_nc(), {"https://example.com/m.bin": {"save_path": str(tmp_path / "m.bin")}}, 0)
        return [call[0][0] for call in sleep.call_args_list]

    def test_follows_retry_after_seconds(self, tmp_path):
        assert self._waited(tmp_path, _throttled(retry_after="7")) == [7]

    def test_caps_an_unreasonable_retry_after(self, tmp_path):
        assert self._waited(tmp_path, _throttled(retry_after="3600")) == [MODEL_FETCH_MAX_DELAY]

    def test_follows_retry_after_as_http_date(self, tmp_path):
        soon = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=5), usegmt=True)
        assert 0 < self._waited(tmp_path, _throttled(retry_after=soon))[0] <= 10

    def test_ignores_a_retry_after_in_the_past(self, tmp_path):
        past = format_datetime(datetime.now(timezone.utc) - timedelta(seconds=30), usegmt=True)
        assert self._waited(tmp_path, _throttled(retry_after=past)) == [1]

    def test_ignores_a_malformed_retry_after(self, tmp_path):
        assert self._waited(tmp_path, _throttled(retry_after="soon")) == [1]

    def test_falls_back_to_exponential_backoff(self, tmp_path):
        assert self._waited(tmp_path, _throttled(), _throttled(), _throttled()) == [1, 2, 4]
