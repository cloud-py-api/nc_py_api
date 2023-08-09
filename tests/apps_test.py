import pytest
from gfixture import NC_TO_TEST

from nc_py_api import Nextcloud

APP_NAME = "files_trashbin"


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_list_apps_types(nc):
    assert isinstance(nc.apps.get_list(), list)
    assert isinstance(nc.apps.get_list(enabled=True), list)
    assert isinstance(nc.apps.get_list(enabled=False), list)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_list_apps(nc):
    apps = nc.apps.get_list()
    assert apps
    assert APP_NAME in apps


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_enable_disable_app(nc):
    assert nc.apps.is_installed(APP_NAME)
    if nc.apps.is_enabled(APP_NAME):
        nc.apps.disable(APP_NAME)
    assert nc.apps.is_disabled(APP_NAME)
    assert not nc.apps.is_enabled(APP_NAME)
    assert nc.apps.is_installed(APP_NAME)
    nc.apps.enable(APP_NAME)
    assert nc.apps.is_enabled(APP_NAME)
    assert nc.apps.is_installed(APP_NAME)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_is_installed_enabled(nc):
    assert nc.apps.is_enabled(APP_NAME) != nc.apps.is_disabled(APP_NAME)
    assert nc.apps.is_installed(APP_NAME)


@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_invalid_param(nc):
    with pytest.raises(ValueError):
        nc.apps.is_enabled("")
    with pytest.raises(ValueError):
        nc.apps.is_installed("")
    with pytest.raises(ValueError):
        nc.apps.is_disabled("")
    with pytest.raises(ValueError):
        nc.apps.enable("")
    with pytest.raises(ValueError):
        nc.apps.disable("")
    with pytest.raises(ValueError):
        nc.apps.ex_app_is_enabled("")
    with pytest.raises(ValueError):
        nc.apps.ex_app_is_disabled("")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_ex_app_get_list(nc):
    if "app_ecosystem_v2" not in nc.capabilities:
        pytest.skip("app_ecosystem_v2 is not installed.")
    enabled_ex_apps = nc.apps.ex_app_get_list(enabled=True)
    assert isinstance(enabled_ex_apps, list)
    for i in enabled_ex_apps:
        assert i.enabled is True
        assert nc.apps.ex_app_is_enabled(i.app_id) is True
        assert nc.apps.ex_app_is_disabled(i.app_id) is False
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
        assert isinstance(app.last_check_time, int)
        assert isinstance(app.system, bool)
        if app.app_id == "nc_py_api":
            assert app.system is True
