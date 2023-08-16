import os
import sys
from subprocess import Popen

import pytest
from _install_wait import check_heartbeat
from gfixture import NC_APP, NC_TO_TEST

from nc_py_api import Nextcloud

# These tests should be run last, as they can affect further one.


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
@pytest.mark.skipif(NC_APP is None, reason="Not available without NextcloudApp.")
def test_ex_app_enable_disable(nc):
    child_environment = os.environ.copy()
    child_environment["APP_PORT"] = os.environ.get("APP_PORT", "9009")
    r = Popen(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_install_only_enabled_handler.py")],
        env=child_environment,
        cwd=os.getcwd(),
    )
    url = f"http://127.0.0.1:{child_environment['APP_PORT']}/heartbeat"
    try:
        if check_heartbeat(url, '"status":"ok"', 15, 0.3):
            raise RuntimeError("`_install_only_enabled_handler` can not start.")
        if nc.apps.ex_app_is_enabled("nc_py_api"):
            nc.apps.ex_app_disable("nc_py_api")
        assert nc.apps.ex_app_is_disabled("nc_py_api") is True
        assert nc.apps.ex_app_is_enabled("nc_py_api") is False
        nc.apps.ex_app_enable("nc_py_api")
        assert nc.apps.ex_app_is_disabled("nc_py_api") is False
        assert nc.apps.ex_app_is_enabled("nc_py_api") is True
    finally:
        r.terminate()
