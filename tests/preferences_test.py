import pytest
from gfixture import NC_TO_TEST

from nc_py_api import NextcloudException


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_available(nc):
    assert nc.preferences_api.available


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_preferences_set(nc):
    if not nc.preferences_api.available:
        pytest.skip("preferences_api is not available")
    nc.preferences_api.set_value("dav", key="user_status_automation", value="yes")
    with pytest.raises(NextcloudException):
        nc.preferences_api.set_value("non_existing_app", "some_cfg_name", "2")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_preferences_delete(nc):
    if not nc.preferences_api.available:
        pytest.skip("preferences_api is not available")
    nc.preferences_api.delete("dav", key="user_status_automation")
    with pytest.raises(NextcloudException):
        nc.preferences_api.delete("non_existing_app", "some_cfg_name")
