import logging
from copy import deepcopy
from unittest import mock

import pytest

from nc_py_api.ex_app import LogLvl, setup_nextcloud_logging


def test_loglvl_values():
    assert LogLvl.FATAL == 4
    assert LogLvl.ERROR == 3
    assert LogLvl.WARNING == 2
    assert LogLvl.INFO == 1
    assert LogLvl.DEBUG == 0


def test_log_success(nc_app):
    nc_app.log(LogLvl.FATAL, "log success")


@pytest.mark.asyncio(scope="session")
async def test_log_success_async(anc_app):
    await anc_app.log(LogLvl.FATAL, "log success")


def test_loglvl_str(nc_app):
    nc_app.log("1", "lolglvl in str: should be written")  # noqa


@pytest.mark.asyncio(scope="session")
async def test_loglvl_str_async(anc_app):
    await anc_app.log("1", "lolglvl in str: should be written")  # noqa


def test_invalid_log_level(nc_app):
    with pytest.raises(ValueError):
        nc_app.log(5, "wrong log level")  # noqa


@pytest.mark.asyncio(scope="session")
async def test_invalid_log_level_async(anc_app):
    with pytest.raises(ValueError):
        await anc_app.log(5, "wrong log level")  # noqa


def test_empty_log(nc_app):
    nc_app.log(LogLvl.FATAL, "")


@pytest.mark.asyncio(scope="session")
async def test_empty_log_async(anc_app):
    await anc_app.log(LogLvl.FATAL, "")


def test_loglvl_equal(nc_app):
    current_log_lvl = nc_app.capabilities["app_api"].get("loglevel", LogLvl.FATAL)
    nc_app.log(current_log_lvl, "log should be written")


@pytest.mark.asyncio(scope="session")
async def test_loglvl_equal_async(anc_app):
    current_log_lvl = (await anc_app.capabilities)["app_api"].get("loglevel", LogLvl.FATAL)
    await anc_app.log(current_log_lvl, "log should be written")


def test_loglvl_less(nc_app):
    current_log_lvl = nc_app.capabilities["app_api"].get("loglevel", LogLvl.FATAL)
    if current_log_lvl == LogLvl.DEBUG:
        pytest.skip("Log lvl to low")
    with mock.patch("tests.conftest.NC_APP._session.ocs") as ocs:
        nc_app.log(int(current_log_lvl) - 1, "will not be sent")  # noqa
        ocs.assert_not_called()
        nc_app.log(current_log_lvl, "will be sent")
        assert ocs.call_count > 0


@pytest.mark.asyncio(scope="session")
async def test_loglvl_less_async(anc_app):
    current_log_lvl = (await anc_app.capabilities)["app_api"].get("loglevel", LogLvl.FATAL)
    if current_log_lvl == LogLvl.DEBUG:
        pytest.skip("Log lvl to low")
    with mock.patch("tests.conftest.NC_APP_ASYNC._session.ocs") as ocs:
        await anc_app.log(int(current_log_lvl) - 1, "will not be sent")  # noqa
        ocs.assert_not_called()
        await anc_app.log(current_log_lvl, "will be sent")
        assert ocs.call_count > 0


def test_log_without_app_api(nc_app):
    srv_capabilities = deepcopy(nc_app.capabilities)
    srv_version = deepcopy(nc_app.srv_version)
    log_lvl = srv_capabilities["app_api"].pop("loglevel")
    srv_capabilities.pop("app_api")
    patched_capabilities = {"capabilities": srv_capabilities, "version": srv_version}
    with (
        mock.patch.dict("tests.conftest.NC_APP._session._capabilities", patched_capabilities, clear=True),
        mock.patch("tests.conftest.NC_APP._session.ocs") as ocs,
    ):
        nc_app.log(log_lvl, "will not be sent")
        ocs.assert_not_called()


@pytest.mark.asyncio(scope="session")
async def test_log_without_app_api_async(anc_app):
    srv_capabilities = deepcopy(await anc_app.capabilities)
    srv_version = deepcopy(await anc_app.srv_version)
    log_lvl = srv_capabilities["app_api"].pop("loglevel")
    srv_capabilities.pop("app_api")
    patched_capabilities = {"capabilities": srv_capabilities, "version": srv_version}
    with (
        mock.patch.dict("tests.conftest.NC_APP_ASYNC._session._capabilities", patched_capabilities, clear=True),
        mock.patch("tests.conftest.NC_APP_ASYNC._session.ocs") as ocs,
    ):
        await anc_app.log(log_lvl, "will not be sent")
        ocs.assert_not_called()


def test_logging(nc_app):
    log_handler = setup_nextcloud_logging("my_logger")
    logger = logging.getLogger("my_logger")
    logger.fatal("testing logging.fatal")
    try:
        a = b  # noqa
    except Exception:  # noqa
        logger.exception("testing logger.exception")
    logger.removeHandler(log_handler)


def test_recursive_logging(nc_app):
    logging.getLogger("niquests").setLevel(logging.DEBUG)
    log_handler = setup_nextcloud_logging()
    logger = logging.getLogger()
    logger.fatal("testing logging.fatal")
    logger.removeHandler(log_handler)
    logging.getLogger("niquests").setLevel(logging.ERROR)
