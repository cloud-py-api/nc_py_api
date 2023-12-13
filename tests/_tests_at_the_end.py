import os
import sys
from subprocess import Popen

import pytest

from ._install_wait import check_heartbeat

# These tests will be run separate, and at the end of all other tests.


@pytest.mark.parametrize("file_to_test", ("_install_only_enabled_handler.py", "_install_only_enabled_handler_async.py"))
def test_ex_app_enable_disable(nc_client, nc_app, file_to_test):
    child_environment = os.environ.copy()
    child_environment["APP_PORT"] = os.environ.get("APP_PORT", "9009")
    r = Popen(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), file_to_test)],
        env=child_environment,
        cwd=os.getcwd(),
    )
    url = f"http://127.0.0.1:{child_environment['APP_PORT']}/heartbeat"
    try:
        if check_heartbeat(url, '"status":"ok"', 15, 0.3):
            raise RuntimeError(f"`{file_to_test}` can not start.")
        if nc_client.apps.ex_app_is_enabled("nc_py_api"):
            nc_client.apps.ex_app_disable("nc_py_api")
        assert nc_client.apps.ex_app_is_disabled("nc_py_api") is True
        assert nc_client.apps.ex_app_is_enabled("nc_py_api") is False
        nc_client.apps.ex_app_enable("nc_py_api")
        assert nc_client.apps.ex_app_is_disabled("nc_py_api") is False
        assert nc_client.apps.ex_app_is_enabled("nc_py_api") is True
    finally:
        r.terminate()
        r.wait(timeout=10)
