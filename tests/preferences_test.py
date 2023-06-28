import pytest

from nc_py_api import NextcloudException

from gfixture import NC_TO_TEST


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_avalaible(nc):
    assert nc.preferences_api.avalaible


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_preferences_set(nc):
    if not nc.preferences_api.avalaible:
        pytest.skip("preferences_api is not avalaible")
    nc.preferences_api.set("dav", key="user_status_automation", value="yes")
    with pytest.raises(NextcloudException):
        nc.preferences_api.set("non_existing_app", "some_cfg_name", "2")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_preferences_delete(nc):
    if not nc.preferences_api.avalaible:
        pytest.skip("preferences_api is not avalaible")
    nc.preferences_api.delete("dav", key="user_status_automation")
    with pytest.raises(NextcloudException):
        nc.preferences_api.delete("non_existing_app", "some_cfg_name")
