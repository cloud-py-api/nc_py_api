"""Tests for model file download with FileLock and atomic rename."""

import hashlib
import os
from threading import Thread
from unittest import mock

import pytest
from filelock import FileLock

from nc_py_api._exceptions import ModelFetchError
from nc_py_api.ex_app.integration_fastapi import fetch_models_task


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

    def iter_raw(self, _chunk_size):
        yield self.content

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

    def test_progress_updates_sent(self, tmp_path):
        save_path = str(tmp_path / "model.bin")
        nc = _mock_nc()

        with mock.patch("nc_py_api.ex_app.integration_fastapi.niquests.get", return_value=FakeResponse(b"data")):
            fetch_models_task(nc, {"https://example.com/m.bin": {"save_path": save_path}}, 0)

        # set_init_status should be called at least for completion (100)
        assert nc.set_init_status.called
        # Last call should be 100 (completion)
        assert nc.set_init_status.call_args_list[-1] == mock.call(100)
