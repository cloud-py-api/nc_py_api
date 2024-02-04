from os import environ
from unittest import mock

import pytest

from nc_py_api.ex_app import set_handlers


def test_get_users_list(nc_app):
    users = nc_app.users_list()
    assert users
    assert nc_app.user in users


@pytest.mark.asyncio(scope="session")
async def test_get_users_list_async(anc_app):
    users = await anc_app.users_list()
    assert users
    assert await anc_app.user in users


def test_app_cfg(nc_app):
    app_cfg = nc_app.app_cfg
    assert app_cfg.app_name == environ["APP_ID"]
    assert app_cfg.app_version == environ["APP_VERSION"]
    assert app_cfg.app_secret == environ["APP_SECRET"]


@pytest.mark.asyncio(scope="session")
async def test_app_cfg_async(anc_app):
    app_cfg = anc_app.app_cfg
    assert app_cfg.app_name == environ["APP_ID"]
    assert app_cfg.app_version == environ["APP_VERSION"]
    assert app_cfg.app_secret == environ["APP_SECRET"]


def test_change_user(nc_app):
    orig_user = nc_app.user
    try:
        orig_capabilities = nc_app.capabilities
        assert nc_app.user_status.available
        nc_app.set_user("")
        assert not nc_app.user_status.available
        assert orig_capabilities != nc_app.capabilities
    finally:
        nc_app.set_user(orig_user)
    assert orig_capabilities == nc_app.capabilities


@pytest.mark.asyncio(scope="session")
async def test_change_user_async(anc_app):
    orig_user = await anc_app.user
    try:
        orig_capabilities = await anc_app.capabilities
        assert await anc_app.user_status.available
        await anc_app.set_user("")
        assert not await anc_app.user_status.available
        assert orig_capabilities != await anc_app.capabilities
    finally:
        await anc_app.set_user(orig_user)
    assert orig_capabilities == await anc_app.capabilities


def test_set_user_same_value(nc_app):
    with (mock.patch("tests.conftest.NC_APP._session.update_server_info") as update_server_info,):
        nc_app.set_user(nc_app.user)
        update_server_info.assert_not_called()


@pytest.mark.asyncio(scope="session")
async def test_set_user_same_value_async(anc_app):
    with (mock.patch("tests.conftest.NC_APP_ASYNC._session.update_server_info") as update_server_info,):
        await anc_app.set_user(await anc_app.user)
        update_server_info.assert_not_called()


def test_set_handlers_invalid_param(nc_any):
    with pytest.raises(ValueError):
        set_handlers(None, None, init_handler=set_handlers, models_to_fetch={"some": {}})  # noqa
