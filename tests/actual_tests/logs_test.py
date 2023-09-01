from copy import deepcopy
from unittest import mock

import pytest

from nc_py_api import NextcloudException
from nc_py_api.ex_app import LogLvl


def test_loglvl_values():
    assert LogLvl.FATAL == 4
    assert LogLvl.ERROR == 3
    assert LogLvl.WARNING == 2
    assert LogLvl.INFO == 1
    assert LogLvl.DEBUG == 0


def test_log_success(nc_app):
    nc_app.log(LogLvl.FATAL, "log success")


def test_loglvl_str(nc_app):
    nc_app.log("1", "lolglvl in str: should be written")  # noqa


def test_invalid_log_level(nc_app):
    with pytest.raises(NextcloudException):
        nc_app.log(5, "wrong log level")  # noqa


def test_empty_log(nc_app):
    nc_app.log(LogLvl.FATAL, "")


def test_loglvl_equal(nc_app):
    current_log_lvl = nc_app.capabilities["app_ecosystem_v2"].get("loglevel", LogLvl.FATAL)
    nc_app.log(current_log_lvl, "log should be written")


def test_loglvl_less(nc_app):
    current_log_lvl = nc_app.capabilities["app_ecosystem_v2"].get("loglevel", LogLvl.FATAL)
    if current_log_lvl == LogLvl.DEBUG:
        pytest.skip("Log lvl to low")
    with mock.patch("tests.conftest.NC_APP._session._ocs") as _ocs:
        nc_app.log(int(current_log_lvl) - 1, "will not be sent")  # noqa
        _ocs.assert_not_called()
        nc_app.log(current_log_lvl, "will be sent")
        assert _ocs.call_count > 0


def test_log_without_app_ecosystem_v2(nc_app):
    srv_capabilities = deepcopy(nc_app.capabilities)
    srv_version = deepcopy(nc_app.srv_version)
    log_lvl = srv_capabilities["app_ecosystem_v2"].pop("loglevel")
    srv_capabilities.pop("app_ecosystem_v2")
    patched_capabilities = {"capabilities": srv_capabilities, "version": srv_version}
    with (
        mock.patch.dict("tests.conftest.NC_APP._session._capabilities", patched_capabilities, clear=True),
        mock.patch("tests.conftest.NC_APP._session._ocs") as _ocs,
    ):
        nc_app.log(log_lvl, "will not be sent")
        _ocs.assert_not_called()
