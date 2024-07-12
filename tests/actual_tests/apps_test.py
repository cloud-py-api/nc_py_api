import datetime

import pytest

from nc_py_api.apps import ExAppInfo

APP_NAME = "files_trashbin"


def test_list_apps_types(nc):
    assert isinstance(nc.apps.get_list(), list)
    assert isinstance(nc.apps.get_list(enabled=True), list)
    assert isinstance(nc.apps.get_list(enabled=False), list)


@pytest.mark.asyncio(scope="session")
async def test_list_apps_types_async(anc):
    assert isinstance(await anc.apps.get_list(), list)
    assert isinstance(await anc.apps.get_list(enabled=True), list)
    assert isinstance(await anc.apps.get_list(enabled=False), list)


def test_list_apps(nc):
    apps = nc.apps.get_list()
    assert apps
    assert APP_NAME in apps


@pytest.mark.asyncio(scope="session")
async def test_list_apps_async(anc):
    apps = await anc.apps.get_list()
    assert apps
    assert APP_NAME in apps


def test_app_enable_disable(nc_client):
    assert nc_client.apps.is_installed(APP_NAME) is True
    if nc_client.apps.is_enabled(APP_NAME):
        nc_client.apps.disable(APP_NAME)
    assert nc_client.apps.is_disabled(APP_NAME) is True
    assert nc_client.apps.is_enabled(APP_NAME) is False
    assert nc_client.apps.is_installed(APP_NAME) is True
    nc_client.apps.enable(APP_NAME)
    assert nc_client.apps.is_enabled(APP_NAME) is True
    assert nc_client.apps.is_installed(APP_NAME) is True


@pytest.mark.asyncio(scope="session")
async def test_app_enable_disable_async(anc_client):
    assert await anc_client.apps.is_installed(APP_NAME) is True
    if await anc_client.apps.is_enabled(APP_NAME):
        await anc_client.apps.disable(APP_NAME)
    assert await anc_client.apps.is_disabled(APP_NAME) is True
    assert await anc_client.apps.is_enabled(APP_NAME) is False
    assert await anc_client.apps.is_installed(APP_NAME) is True
    await anc_client.apps.enable(APP_NAME)
    assert await anc_client.apps.is_enabled(APP_NAME) is True
    assert await anc_client.apps.is_installed(APP_NAME) is True


def test_is_installed_enabled(nc):
    assert nc.apps.is_enabled(APP_NAME) != nc.apps.is_disabled(APP_NAME)
    assert nc.apps.is_installed(APP_NAME)


@pytest.mark.asyncio(scope="session")
async def test_is_installed_enabled_async(anc):
    assert await anc.apps.is_enabled(APP_NAME) != await anc.apps.is_disabled(APP_NAME)
    assert await anc.apps.is_installed(APP_NAME)


def test_invalid_param(nc_any):
    with pytest.raises(ValueError):
        nc_any.apps.is_enabled("")
    with pytest.raises(ValueError):
        nc_any.apps.is_installed("")
    with pytest.raises(ValueError):
        nc_any.apps.is_disabled("")
    with pytest.raises(ValueError):
        nc_any.apps.enable("")
    with pytest.raises(ValueError):
        nc_any.apps.disable("")
    with pytest.raises(ValueError):
        nc_any.apps.ex_app_is_enabled("")
    with pytest.raises(ValueError):
        nc_any.apps.ex_app_is_disabled("")
    with pytest.raises(ValueError):
        nc_any.apps.ex_app_disable("")
    with pytest.raises(ValueError):
        nc_any.apps.ex_app_enable("")


@pytest.mark.asyncio(scope="session")
async def test_invalid_param_async(anc_any):
    with pytest.raises(ValueError):
        await anc_any.apps.is_enabled("")
    with pytest.raises(ValueError):
        await anc_any.apps.is_installed("")
    with pytest.raises(ValueError):
        await anc_any.apps.is_disabled("")
    with pytest.raises(ValueError):
        await anc_any.apps.enable("")
    with pytest.raises(ValueError):
        await anc_any.apps.disable("")
    with pytest.raises(ValueError):
        await anc_any.apps.ex_app_is_enabled("")
    with pytest.raises(ValueError):
        await anc_any.apps.ex_app_is_disabled("")
    with pytest.raises(ValueError):
        await anc_any.apps.ex_app_disable("")
    with pytest.raises(ValueError):
        await anc_any.apps.ex_app_enable("")


def _test_ex_app_get_list(ex_apps: list[ExAppInfo], enabled_ex_apps: list[ExAppInfo]):
    assert isinstance(ex_apps, list)
    assert "nc_py_api" in [i.app_id for i in ex_apps]
    assert len(ex_apps) >= len(enabled_ex_apps)
    for app in ex_apps:
        assert isinstance(app.app_id, str)
        assert isinstance(app.name, str)
        assert isinstance(app.version, str)
        assert isinstance(app.enabled, bool)
        assert isinstance(app.last_check_time, datetime.datetime)
        assert str(app).find("id=") != -1 and str(app).find("ver=") != -1


def test_ex_app_get_list(nc, nc_app):
    enabled_ex_apps = nc.apps.ex_app_get_list(enabled=True)
    assert isinstance(enabled_ex_apps, list)
    for i in enabled_ex_apps:
        assert i.enabled is True
    assert "nc_py_api" in [i.app_id for i in enabled_ex_apps]
    ex_apps = nc.apps.ex_app_get_list()
    _test_ex_app_get_list(ex_apps, enabled_ex_apps)


@pytest.mark.asyncio(scope="session")
async def test_ex_app_get_list_async(anc, anc_app):
    enabled_ex_apps = await anc.apps.ex_app_get_list(enabled=True)
    assert isinstance(enabled_ex_apps, list)
    for i in enabled_ex_apps:
        assert i.enabled is True
    assert "nc_py_api" in [i.app_id for i in enabled_ex_apps]
    ex_apps = await anc.apps.ex_app_get_list()
    _test_ex_app_get_list(ex_apps, enabled_ex_apps)
