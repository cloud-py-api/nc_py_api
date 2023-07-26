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


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_ex_app_get_list(nc):
    if "app_ecosystem_v2" not in nc.capabilities:
        pytest.skip("app_ecosystem_v2 is not installed.")
    ex_apps = nc.apps.ex_app_get_list()
    assert isinstance(ex_apps, list)
    assert isinstance(ex_apps[0], str)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_ex_app_get_info(nc):
    if "app_ecosystem_v2" not in nc.capabilities:
        pytest.skip("app_ecosystem_v2 is not installed.")
    ex_apps = nc.apps.ex_app_get_info()
    assert isinstance(ex_apps, list)
    nc_py_api = [i for i in ex_apps if i["id"] == "nc_py_api"][0]
    assert nc_py_api["id"] == "nc_py_api"
    assert isinstance(nc_py_api["name"], str)
    assert isinstance(nc_py_api["version"], str)
    assert nc_py_api["enabled"]
    assert isinstance(nc_py_api["last_check_time"], int)
    assert nc_py_api["system"]
