import datetime

import pytest

APP_NAME = "files_trashbin"


def test_list_apps_types(nc):
    assert isinstance(nc.apps.get_list(), list)
    assert isinstance(nc.apps.get_list(enabled=True), list)
    assert isinstance(nc.apps.get_list(enabled=False), list)


def test_list_apps(nc):
    apps = nc.apps.get_list()
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


def test_is_installed_enabled(nc):
    assert nc.apps.is_enabled(APP_NAME) != nc.apps.is_disabled(APP_NAME)
    assert nc.apps.is_installed(APP_NAME)


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


def test_ex_app_get_list(nc, nc_app):
    enabled_ex_apps = nc.apps.ex_app_get_list(enabled=True)
    assert isinstance(enabled_ex_apps, list)
    for i in enabled_ex_apps:
        assert i.enabled is True
    assert "nc_py_api" in [i.app_id for i in enabled_ex_apps]
    ex_apps = nc.apps.ex_app_get_list()
    assert isinstance(ex_apps, list)
    assert "nc_py_api" in [i.app_id for i in ex_apps]
    assert len(ex_apps) >= len(enabled_ex_apps)
    for app in ex_apps:
        assert isinstance(app.app_id, str)
        assert isinstance(app.name, str)
        assert isinstance(app.version, str)
        assert isinstance(app.enabled, bool)
        assert isinstance(app.last_check_time, datetime.datetime)
        assert isinstance(app.system, bool)
        if app.app_id == "nc_py_api":
            assert app.system is True
