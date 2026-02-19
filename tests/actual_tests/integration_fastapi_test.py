import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from filelock import SoftFileLock, Timeout

from nc_py_api._exceptions import ModelFetchError
from nc_py_api.ex_app import integration_fastapi
from nc_py_api.ex_app.integration_fastapi import fetch_models_task


class TestFetchModelAsFile:
    """Tests for __fetch_model_as_file function."""

    def test_download_new_file_success(self, nc_app):
        """Test successful download of a new file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                test_url = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/refs/heads/main/LICENSE.txt"
                models = {test_url: {"save_path": "test_license.txt"}}

                fetch_models_task(nc_app, models, 0)

                assert Path("test_license.txt").exists()
                assert Path("test_license.txt").stat().st_size > 0
                assert not Path("test_license.txt.tmp").exists()
                assert not Path("test_license.txt.lock").exists()  # Lock should be released
            finally:
                os.chdir(original_cwd)

    def test_download_uses_temp_file(self, nc_app):
        """Test that download uses temporary file and atomically renames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                test_url = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/refs/heads/main/LICENSE.txt"
                models = {test_url: {"save_path": "test_file.txt"}}

                # Track if temp file was created during download
                temp_file_existed = []
                original_replace = os.replace

                def track_replace(src, dst):
                    temp_file_existed.append(Path(src).exists())
                    return original_replace(src, dst)

                with patch("nc_py_api.ex_app.integration_fastapi.os.replace", side_effect=track_replace):
                    fetch_models_task(nc_app, models, 0)

                assert temp_file_existed[0] is True  # temp file existed before rename
                assert Path("test_file.txt").exists()
                assert not Path("test_file.txt.tmp").exists()  # temp file cleaned up
            finally:
                os.chdir(original_cwd)

    def test_skip_download_if_file_valid(self, nc_app):
        """Test that download is skipped if file already exists and matches ETag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                test_url = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/refs/heads/main/LICENSE.txt"
                models = {test_url: {"save_path": "cached_file.txt"}}

                # First download
                fetch_models_task(nc_app, models, 0)
                first_mtime = Path("cached_file.txt").stat().st_mtime

                # Second download should skip
                fetch_models_task(nc_app, models, 0)
                second_mtime = Path("cached_file.txt").stat().st_mtime

                # File should not be re-downloaded (mtime unchanged)
                assert first_mtime == second_mtime
            finally:
                os.chdir(original_cwd)

    def test_lock_timeout(self, nc_app):
        """Test that lock times out when file is already locked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                test_url = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/refs/heads/main/LICENSE.txt"
                models = {test_url: {"save_path": "locked_file.txt"}}

                # Temporarily set a short timeout for testing
                original_timeout = integration_fastapi.LOCK_TIMEOUT
                integration_fastapi.LOCK_TIMEOUT = 1  # 1 second timeout

                # Acquire lock in a background thread to simulate another pod
                lock = SoftFileLock("locked_file.txt.lock")
                lock.acquire()

                def release_after_delay():
                    time.sleep(3)  # Hold lock longer than timeout
                    lock.release()

                thread = threading.Thread(target=release_after_delay, daemon=True)
                thread.start()

                try:
                    # Try to download while locked - should timeout
                    with pytest.raises(ModelFetchError) as exc_info:
                        fetch_models_task(nc_app, models, 0)
                    # The underlying exception should be a Timeout
                    assert "Timeout" in str(exc_info.value.__cause__) or isinstance(exc_info.value.__cause__, Timeout)
                finally:
                    integration_fastapi.LOCK_TIMEOUT = original_timeout
                    thread.join(timeout=5)
            finally:
                os.chdir(original_cwd)

    def test_invalid_url_raises_error(self, nc_app):
        """Test that invalid URL raises ModelFetchError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                test_url = "https://nonexistent.example.com/invalid/model.bin"
                models = {test_url: {"save_path": "invalid_model.bin"}}

                with pytest.raises(ModelFetchError):
                    fetch_models_task(nc_app, models, 0)
            finally:
                os.chdir(original_cwd)

    def test_progress_updates(self, nc_app):
        """Test that progress is updated during download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                test_url = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/refs/heads/main/LICENSE.txt"
                models = {test_url: {"save_path": "progress_test.txt"}}

                progress_calls = []
                original_set_init = nc_app.set_init_status

                def track_progress(progress, *args):
                    progress_calls.append(progress)
                    return original_set_init(progress, *args) if args else original_set_init(progress)

                with patch.object(nc_app, "set_init_status", side_effect=track_progress):
                    fetch_models_task(nc_app, models, 0)

                # Should have progress updates including final 100
                assert len(progress_calls) > 0
                assert progress_calls[-1] == 100
            finally:
                os.chdir(original_cwd)

    def test_concurrent_downloads_serialized(self, nc_app):
        """Test that concurrent download attempts are serialized by the lock."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                test_url = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/refs/heads/main/LICENSE.txt"
                models = {test_url: {"save_path": "concurrent_test.txt"}}

                # Track download events
                download_events = []
                download_lock = threading.Lock()

                # Patch niquests.get to track when downloads actually happen
                original_get = __import__("niquests").get

                def tracked_get(*args, **kwargs):
                    with download_lock:
                        download_events.append(("start", threading.current_thread().name, time.time()))
                    result = original_get(*args, **kwargs)
                    with download_lock:
                        download_events.append(("end", threading.current_thread().name, time.time()))
                    return result

                with patch("niquests.get", side_effect=tracked_get):
                    # Simulate two pods trying to download simultaneously
                    results = []
                    errors = []

                    def download_in_thread(thread_name):
                        try:
                            fetch_models_task(nc_app, models.copy(), 0)
                            results.append(thread_name)
                        except Exception as e:
                            errors.append((thread_name, e))

                    thread1 = threading.Thread(target=download_in_thread, args=("pod-1",), name="pod-1")
                    thread2 = threading.Thread(target=download_in_thread, args=("pod-2",), name="pod-2")

                    # Start both threads at the same time
                    thread1.start()
                    thread2.start()

                    thread1.join(timeout=30)
                    thread2.join(timeout=30)

                    # Verify both threads completed
                    assert len(results) + len(errors) == 2, f"Not all threads completed: {results}, {errors}"
                    assert len(errors) == 0, f"Threads failed with errors: {errors}"

                    # Check that downloads were serialized (not concurrent)
                    start_events = [e for e in download_events if e[0] == "start"]
                    end_events = [e for e in download_events if e[0] == "end"]

                    if len(start_events) == 2:
                        # If two downloads happened, they should be sequential
                        first_end_time = end_events[0][2]
                        second_start_time = start_events[1][2]
                        # Second download should start after first ends (serialized)
                        assert second_start_time >= first_end_time, "Downloads happened concurrently instead of serially"
                    elif len(start_events) == 1:
                        # Only one download happened - the other thread reused the file (also valid)
                        pass
                    else:
                        pytest.fail(f"Unexpected number of download events: {download_events}")

                    # Verify file was downloaded successfully
                    assert Path("concurrent_test.txt").exists()
                    assert Path("concurrent_test.txt").stat().st_size > 0
            finally:
                os.chdir(original_cwd)


class TestFetchModelAsSnapshot:
    """Tests for __fetch_model_as_snapshot function."""

    def test_snapshot_download_success(self, nc_app):
        """Test successful HuggingFace snapshot download."""
        pytest.importorskip("huggingface_hub")
        pytest.importorskip("tqdm")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                # Use a very small model for testing
                model_name = "hf-internal-testing/tiny-random-gpt2"
                cache_dir = Path(tmpdir) / "hf_cache"
                models = {model_name: {"cache_dir": str(cache_dir), "max_workers": 1}}

                fetch_models_task(nc_app, models, 0)

                # Check that model was downloaded
                assert cache_dir.exists()
                assert models[model_name]["path"]  # Should have path set
                assert not Path(cache_dir / f"{model_name.replace('/', '_')}.lock").exists()  # Lock released
            finally:
                os.chdir(original_cwd)

    def test_snapshot_lock_timeout(self, nc_app):
        """Test that snapshot download lock times out when locked."""
        pytest.importorskip("huggingface_hub")
        pytest.importorskip("tqdm")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                model_name = "hf-internal-testing/tiny-random-gpt2"
                cache_dir = Path(tmpdir) / "hf_cache"
                cache_dir.mkdir()
                models = {model_name: {"cache_dir": str(cache_dir)}}

                # Temporarily set a short timeout for testing
                original_timeout = integration_fastapi.LOCK_TIMEOUT
                integration_fastapi.LOCK_TIMEOUT = 1  # 1 second timeout

                # Acquire lock in background thread
                safe_name = model_name.replace("/", "_")
                lock_path = cache_dir / f"{safe_name}.lock"
                lock = SoftFileLock(str(lock_path))
                lock.acquire()

                def release_after_delay():
                    time.sleep(3)  # Hold lock longer than timeout
                    lock.release()

                thread = threading.Thread(target=release_after_delay, daemon=True)
                thread.start()

                try:
                    with pytest.raises(ModelFetchError) as exc_info:
                        fetch_models_task(nc_app, models, 0)
                    # The underlying exception should be a Timeout
                    assert "Timeout" in str(exc_info.value.__cause__) or isinstance(exc_info.value.__cause__, Timeout)
                finally:
                    integration_fastapi.LOCK_TIMEOUT = original_timeout
                    thread.join(timeout=5)
            finally:
                os.chdir(original_cwd)

    def test_snapshot_progress_updates(self, nc_app):
        """Test that progress is updated during snapshot download."""
        pytest.importorskip("huggingface_hub")
        pytest.importorskip("tqdm")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                model_name = "hf-internal-testing/tiny-random-gpt2"
                cache_dir = Path(tmpdir) / "hf_cache"
                models = {model_name: {"cache_dir": str(cache_dir), "max_workers": 1}}

                progress_calls = []
                original_set_init = nc_app.set_init_status

                def track_progress(progress, *args):
                    progress_calls.append(progress)
                    return original_set_init(progress, *args) if args else original_set_init(progress)

                with patch.object(nc_app, "set_init_status", side_effect=track_progress):
                    fetch_models_task(nc_app, models, 0)

                # Should have progress updates including final 100
                assert len(progress_calls) > 0
                assert progress_calls[-1] == 100
            finally:
                os.chdir(original_cwd)

    def test_invalid_model_raises_error(self, nc_app):
        """Test that invalid model name raises ModelFetchError."""
        pytest.importorskip("huggingface_hub")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                model_name = "nonexistent-user/nonexistent-model-xyz123"
                cache_dir = Path(tmpdir) / "hf_cache"
                models = {model_name: {"cache_dir": str(cache_dir)}}

                with pytest.raises(ModelFetchError):
                    fetch_models_task(nc_app, models, 0)
            finally:
                os.chdir(original_cwd)

    def test_concurrent_snapshot_downloads_serialized(self, nc_app):
        """Test that concurrent snapshot download attempts are serialized by the lock."""
        pytest.importorskip("huggingface_hub")
        pytest.importorskip("tqdm")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                model_name = "hf-internal-testing/tiny-random-gpt2"
                cache_dir = Path(tmpdir) / "hf_cache"
                models = {model_name: {"cache_dir": str(cache_dir), "max_workers": 1}}

                # Track when snapshot_download is called
                from huggingface_hub import snapshot_download
                download_events = []
                download_lock = threading.Lock()

                original_snapshot_download = snapshot_download

                def tracked_snapshot_download(*args, **kwargs):
                    with download_lock:
                        download_events.append(("start", threading.current_thread().name, time.time()))
                    result = original_snapshot_download(*args, **kwargs)
                    with download_lock:
                        download_events.append(("end", threading.current_thread().name, time.time()))
                    return result

                with patch("nc_py_api.ex_app.integration_fastapi.snapshot_download", side_effect=tracked_snapshot_download):
                    # Simulate two pods trying to download simultaneously
                    results = []
                    errors = []

                    def download_in_thread(thread_name):
                        try:
                            fetch_models_task(nc_app, {model_name: {"cache_dir": str(cache_dir), "max_workers": 1}}, 0)
                            results.append(thread_name)
                        except Exception as e:
                            errors.append((thread_name, e))

                    thread1 = threading.Thread(target=download_in_thread, args=("pod-1",), name="pod-1")
                    thread2 = threading.Thread(target=download_in_thread, args=("pod-2",), name="pod-2")

                    # Start both threads at the same time
                    thread1.start()
                    thread2.start()

                    thread1.join(timeout=60)
                    thread2.join(timeout=60)

                    # Verify both threads completed
                    assert len(results) + len(errors) == 2, f"Not all threads completed: {results}, {errors}"
                    assert len(errors) == 0, f"Threads failed with errors: {errors}"

                    # Check that downloads were serialized (not concurrent)
                    start_events = [e for e in download_events if e[0] == "start"]
                    end_events = [e for e in download_events if e[0] == "end"]

                    if len(start_events) == 2:
                        # If two downloads happened, they should be sequential
                        first_end_time = end_events[0][2]
                        second_start_time = start_events[1][2]
                        # Second download should start after first ends (serialized)
                        assert second_start_time >= first_end_time, "Downloads happened concurrently instead of serially"
                    elif len(start_events) == 1:
                        # Only one download happened - the other thread reused cached model (also valid)
                        pass
                    else:
                        pytest.fail(f"Unexpected number of download events: {download_events}")

                    # Verify model was downloaded successfully
                    assert cache_dir.exists()
            finally:
                os.chdir(original_cwd)


class TestFetchModelsTask:
    """Tests for fetch_models_task function."""

    def test_multiple_models_download(self, nc_app):
        """Test downloading multiple models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                url1 = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/refs/heads/main/LICENSE.txt"
                url2 = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/README.md"
                models = {
                    url1: {"save_path": "file1.txt"},
                    url2: {"save_path": "file2.txt"},
                }

                fetch_models_task(nc_app, models, 0)

                assert Path("file1.txt").exists()
                assert Path("file2.txt").exists()
            finally:
                os.chdir(original_cwd)

    def test_empty_models_dict(self, nc_app):
        """Test that empty models dict completes successfully."""
        fetch_models_task(nc_app, {}, 0)
        # Should not raise any errors

    def test_progress_distribution(self, nc_app):
        """Test that progress is distributed across multiple models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                url1 = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/refs/heads/main/LICENSE.txt"
                url2 = "https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/README.md"
                models = {
                    url1: {"save_path": "file1.txt"},
                    url2: {"save_path": "file2.txt"},
                }

                progress_calls = []
                original_set_init = nc_app.set_init_status

                def track_progress(progress, *args):
                    progress_calls.append(progress)
                    return original_set_init(progress, *args) if args else original_set_init(progress)

                with patch.object(nc_app, "set_init_status", side_effect=track_progress):
                    fetch_models_task(nc_app, models, 0)

                # Progress should go from 0 to 100
                assert progress_calls[-1] == 100
                assert all(0 <= p <= 100 for p in progress_calls)
            finally:
                os.chdir(original_cwd)
