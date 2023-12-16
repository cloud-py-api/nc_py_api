from os import environ
from unittest import mock

import pytest

from nc_py_api.ex_app import ApiScope, set_handlers


def test_get_users_list(nc_app):
    users = nc_app.users_list()
    assert users
    assert nc_app.user in users


@pytest.mark.asyncio(scope="session")
async def test_get_users_list_async(anc_app):
    users = await anc_app.users_list()
    assert users
    assert await anc_app.user in users


def test_scope_allowed(nc_app):
    for i in ApiScope:
        assert nc_app.scope_allowed(i)
    assert not nc_app.scope_allowed(0)  # noqa
    assert not nc_app.scope_allowed(999999999)  # noqa


@pytest.mark.asyncio(scope="session")
async def test_scope_allowed_async(anc_app):
    for i in ApiScope:
        assert await anc_app.scope_allowed(i)
    assert not await anc_app.scope_allowed(0)  # noqa
    assert not await anc_app.scope_allowed(999999999)  # noqa


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


def test_scope_allow_app_ecosystem_disabled(nc_client, nc_app):
    assert nc_app.scope_allowed(ApiScope.FILES)
    nc_client.apps.disable("app_api")
    try:
        assert nc_app.scope_allowed(ApiScope.FILES)
        nc_app.update_server_info()
        assert not nc_app.scope_allowed(ApiScope.FILES)
    finally:
        nc_client.apps.enable("app_api")
        nc_app.update_server_info()


@pytest.mark.asyncio(scope="session")
async def test_scope_allow_app_ecosystem_disabled_async(anc_client, anc_app):
    assert await anc_app.scope_allowed(ApiScope.FILES)
    await anc_client.apps.disable("app_api")
    try:
        assert await anc_app.scope_allowed(ApiScope.FILES)
        await anc_app.update_server_info()
        assert not await anc_app.scope_allowed(ApiScope.FILES)
    finally:
        await anc_client.apps.enable("app_api")
        await anc_app.update_server_info()


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
