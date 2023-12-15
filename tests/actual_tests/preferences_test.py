import pytest

from nc_py_api import NextcloudException


def test_available(nc):
    assert isinstance(nc.preferences.available, bool)


@pytest.mark.asyncio(scope="session")
async def test_available_async(anc):
    assert isinstance(await anc.preferences.available, bool)


def test_preferences_set(nc):
    if not nc.preferences.available:
        pytest.skip("provisioning_api is not available")
    nc.preferences.set_value("dav", key="user_status_automation", value="yes")
    with pytest.raises(NextcloudException):
        nc.preferences.set_value("non_existing_app", "some_cfg_name", "2")


@pytest.mark.asyncio(scope="session")
async def test_preferences_set_async(anc):
    if not await anc.preferences.available:
        pytest.skip("provisioning_api is not available")
    await anc.preferences.set_value("dav", key="user_status_automation", value="yes")
    with pytest.raises(NextcloudException):
        await anc.preferences.set_value("non_existing_app", "some_cfg_name", "2")


def test_preferences_delete(nc):
    if not nc.preferences.available:
        pytest.skip("provisioning_api is not available")
    nc.preferences.delete("dav", key="user_status_automation")
    with pytest.raises(NextcloudException):
        nc.preferences.delete("non_existing_app", "some_cfg_name")


@pytest.mark.asyncio(scope="session")
async def test_preferences_delete_async(anc):
    if not await anc.preferences.available:
        pytest.skip("provisioning_api is not available")
    await anc.preferences.delete("dav", key="user_status_automation")
    with pytest.raises(NextcloudException):
        await anc.preferences.delete("non_existing_app", "some_cfg_name")
