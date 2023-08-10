from copy import deepcopy
from unittest import mock

import pytest
from gfixture import NC_APP

from nc_py_api import NextcloudException
from nc_py_api.ex_app import LogLvl

if NC_APP is None or "app_ecosystem_v2" not in NC_APP.capabilities:
    pytest.skip("app_ecosystem_v2 is not installed.", allow_module_level=True)

AE_CAPABILITIES = NC_APP.capabilities["app_ecosystem_v2"]


def test_loglvl_values():
    assert LogLvl.FATAL == 4
    assert LogLvl.ERROR == 3
    assert LogLvl.WARNING == 2
    assert LogLvl.INFO == 1
    assert LogLvl.DEBUG == 0


def test_log_success():
    NC_APP.log(LogLvl.FATAL, "log success")


def test_loglvl_str():
    NC_APP.log("1", "lolglvl in str: should be written")


def test_invalid_log_level():
    with pytest.raises(NextcloudException):
        NC_APP.log(5, "wrong log level")


def test_empty_log():
    NC_APP.log(LogLvl.FATAL, "")


def test_loglvl_equal():
    NC_APP.log(AE_CAPABILITIES.get("loglevel", LogLvl.FATAL), "log should be written")


@pytest.mark.skipif(AE_CAPABILITIES.get("loglevel", LogLvl.FATAL) == LogLvl.DEBUG, reason="Log lvl to low")
def test_loglvl_less():
    with mock.patch("gfixture.NC_APP._session._ocs") as _ocs:
        NC_APP.log(int(AE_CAPABILITIES["loglevel"]) - 1, "will not be sent")
        _ocs.assert_not_called()
        NC_APP.log(AE_CAPABILITIES["loglevel"], "will be sent")
        assert _ocs.call_count > 0


def test_log_without_app_ecosystem_v2():
    srv_capabilities = deepcopy(NC_APP.capabilities)
    srv_version = deepcopy(NC_APP.srv_version)
    log_lvl = srv_capabilities["app_ecosystem_v2"].pop("loglevel")
    srv_capabilities.pop("app_ecosystem_v2")
    patched_capabilities = {"capabilities": srv_capabilities, "version": srv_version}
    with mock.patch.dict("gfixture.NC_APP._session._capabilities", patched_capabilities, clear=True):
        with mock.patch("gfixture.NC_APP._session._ocs") as _ocs:
            NC_APP.log(log_lvl, "will not be sent")
            _ocs.assert_not_called()
