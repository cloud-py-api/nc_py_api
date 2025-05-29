import pytest

from nc_py_api import NextcloudExceptionNotFound

from ..conftest import NC_APP, NC_APP_ASYNC

if NC_APP is None:
    pytest.skip("Need App mode", allow_module_level=True)


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_get_value_invalid(class_to_test):
    with pytest.raises(ValueError):
        class_to_test.get_value("")


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_get_value_invalid_async(class_to_test):
    with pytest.raises(ValueError):
        await class_to_test.get_value("")


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_get_values_invalid(class_to_test):
    assert class_to_test.get_values([]) == []
    with pytest.raises(ValueError):
        class_to_test.get_values([""])
    with pytest.raises(ValueError):
        class_to_test.get_values(["", "k"])


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_get_values_invalid_async(class_to_test):
    assert await class_to_test.get_values([]) == []
    with pytest.raises(ValueError):
        await class_to_test.get_values([""])
    with pytest.raises(ValueError):
        await class_to_test.get_values(["", "k"])


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_set_empty_key(class_to_test):
    with pytest.raises(ValueError):
        class_to_test.set_value("", "some value")


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_set_empty_key_async(class_to_test):
    with pytest.raises(ValueError):
        await class_to_test.set_value("", "some value")


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_delete_invalid(class_to_test):
    class_to_test.delete([])
    with pytest.raises(ValueError):
        class_to_test.delete([""])
    with pytest.raises(ValueError):
        class_to_test.delete(["", "k"])


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_delete_invalid_async(class_to_test):
    await class_to_test.delete([])
    with pytest.raises(ValueError):
        await class_to_test.delete([""])
    with pytest.raises(ValueError):
        await class_to_test.delete(["", "k"])


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_get_default(class_to_test):
    assert class_to_test.get_value("non_existing_key", default="alice") == "alice"


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_get_default_async(class_to_test):
    assert await class_to_test.get_value("non_existing_key", default="alice") == "alice"


@pytest.mark.parametrize("value", ("0", "1", "12 3", ""))
@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_set_delete(value, class_to_test):
    class_to_test.delete("test_key")
    assert class_to_test.get_value("test_key") is None
    class_to_test.set_value("test_key", value)
    assert class_to_test.get_value("test_key") == value
    class_to_test.set_value("test_key", "zzz")
    assert class_to_test.get_value("test_key") == "zzz"
    class_to_test.delete("test_key")
    assert class_to_test.get_value("test_key") is None


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("value", ("0", "1", "12 3", ""))
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_set_delete_async(value, class_to_test):
    await class_to_test.delete("test_key")
    assert await class_to_test.get_value("test_key") is None
    await class_to_test.set_value("test_key", value)
    assert await class_to_test.get_value("test_key") == value
    await class_to_test.set_value("test_key", "zzz")
    assert await class_to_test.get_value("test_key") == "zzz"
    await class_to_test.delete("test_key")
    assert await class_to_test.get_value("test_key") is None


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_delete(class_to_test):
    class_to_test.set_value("test_key", "123")
    assert class_to_test.get_value("test_key")
    class_to_test.delete("test_key")
    assert class_to_test.get_value("test_key") is None
    class_to_test.delete("test_key")
    class_to_test.delete(["test_key"])
    with pytest.raises(NextcloudExceptionNotFound):
        class_to_test.delete("test_key", not_fail=False)
    with pytest.raises(NextcloudExceptionNotFound):
        class_to_test.delete(["test_key"], not_fail=False)


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_delete_async(class_to_test):
    await class_to_test.set_value("test_key", "123")
    assert await class_to_test.get_value("test_key")
    await class_to_test.delete("test_key")
    assert await class_to_test.get_value("test_key") is None
    await class_to_test.delete("test_key")
    await class_to_test.delete(["test_key"])
    with pytest.raises(NextcloudExceptionNotFound):
        await class_to_test.delete("test_key", not_fail=False)
    with pytest.raises(NextcloudExceptionNotFound):
        await class_to_test.delete(["test_key"], not_fail=False)


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_get(class_to_test):
    class_to_test.delete(["test key", "test key2"])
    assert len(class_to_test.get_values(["test key", "test key2"])) == 0
    class_to_test.set_value("test key", "123")
    assert len(class_to_test.get_values(["test key", "test key2"])) == 1
    class_to_test.set_value("test key2", "123")
    assert len(class_to_test.get_values(["test key", "test key2"])) == 2


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_get_async(class_to_test):
    await class_to_test.delete(["test key", "test key2"])
    assert len(await class_to_test.get_values(["test key", "test key2"])) == 0
    await class_to_test.set_value("test key", "123")
    assert len(await class_to_test.get_values(["test key", "test key2"])) == 1
    await class_to_test.set_value("test key2", "123")
    assert len(await class_to_test.get_values(["test key", "test key2"])) == 2


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_multiply_delete(class_to_test):
    class_to_test.set_value("test_key", "123")
    class_to_test.set_value("test_key2", "123")
    assert len(class_to_test.get_values(["test_key", "test_key2"])) == 2
    class_to_test.delete(["test_key", "test_key2"])
    assert len(class_to_test.get_values(["test_key", "test_key2"])) == 0
    class_to_test.delete(["test_key", "test_key2"])
    class_to_test.set_value("test_key", "123")
    assert len(class_to_test.get_values(["test_key", "test_key2"])) == 1
    class_to_test.delete(["test_key", "test_key2"])
    assert len(class_to_test.get_values(["test_key", "test_key2"])) == 0


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_multiply_delete_async(class_to_test):
    await class_to_test.set_value("test_key", "123")
    await class_to_test.set_value("test_key2", "123")
    assert len(await class_to_test.get_values(["test_key", "test_key2"])) == 2
    await class_to_test.delete(["test_key", "test_key2"])
    assert len(await class_to_test.get_values(["test_key", "test_key2"])) == 0
    await class_to_test.delete(["test_key", "test_key2"])
    await class_to_test.set_value("test_key", "123")
    assert len(await class_to_test.get_values(["test_key", "test_key2"])) == 1
    await class_to_test.delete(["test_key", "test_key2"])
    assert len(await class_to_test.get_values(["test_key", "test_key2"])) == 0


@pytest.mark.parametrize("key", ("k", "k y", " "))
@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_get_non_existing(key, class_to_test):
    class_to_test.delete(key)
    assert class_to_test.get_value(key) is None
    assert class_to_test.get_values([key]) == []
    assert len(class_to_test.get_values([key, "non_existing_key"])) == 0


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("key", ("k", "k y", " "))
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_get_non_existing_async(key, class_to_test):
    await class_to_test.delete(key)
    assert await class_to_test.get_value(key) is None
    assert await class_to_test.get_values([key]) == []
    assert len(await class_to_test.get_values([key, "non_existing_key"])) == 0


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_cfg_ex_get_typing(class_to_test):
    class_to_test.set_value("test key", "123")
    class_to_test.set_value("test key2", "321")
    r = class_to_test.get_values(["test key", "test key2"])
    assert isinstance(r, list)
    assert r[0].key == "test key"
    assert r[1].key == "test key2"
    assert r[0].value == "123"
    assert r[1].value == "321"


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_cfg_ex_get_typing_async(class_to_test):
    await class_to_test.set_value("test key", "123")
    await class_to_test.set_value("test key2", "321")
    r = await class_to_test.get_values(["test key", "test key2"])
    assert isinstance(r, list)
    assert r[0].key == "test key"
    assert r[1].key == "test key2"
    assert r[0].value == "123"
    assert r[1].value == "321"


@pytest.mark.parametrize("class_to_test", (NC_APP.appconfig_ex, NC_APP.preferences_ex))
def test_appcfg_sensitive(nc_app, class_to_test):
    class_to_test.delete("test_key")
    class_to_test.set_value("test_key", "123", sensitive=True)
    assert class_to_test.get_value("test_key") == "123"
    assert class_to_test.get_values(["test_key"])[0].value == "123"
    class_to_test.delete("test_key")
    # next code tests `sensitive` value from the `AppAPI`
    params = {"configKey": "test_key", "configValue": "123"}
    result = nc_app._session.ocs("POST", f"{nc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    if class_to_test == NC_APP.appconfig_ex or nc_app.srv_version["major"] >= 32:
        assert not result["sensitive"]  # by default if sensitive value is unspecified it is False
    class_to_test.delete("test_key")
    params["sensitive"] = True
    result = nc_app._session.ocs("POST", f"{nc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == "123"
    if class_to_test == NC_APP.appconfig_ex or nc_app.srv_version["major"] >= 32:
        assert bool(result["sensitive"]) is True
    params.pop("sensitive")  # if we not specify value, AppEcosystem should not change it.
    result = nc_app._session.ocs("POST", f"{nc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == "123"
    if class_to_test == NC_APP.appconfig_ex or nc_app.srv_version["major"] >= 32:
        assert bool(result["sensitive"]) is True
    params["sensitive"] = False
    result = nc_app._session.ocs("POST", f"{nc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == "123"
    if class_to_test == NC_APP.appconfig_ex or nc_app.srv_version["major"] >= 32:
        assert bool(result["sensitive"]) is False
    # test setting to empty value (sensitive=False)
    params["configValue"] = ""
    result = nc_app._session.ocs("POST", f"{nc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == ""
    if class_to_test == NC_APP.appconfig_ex or nc_app.srv_version["major"] >= 32:
        assert bool(result["sensitive"]) is False
    assert class_to_test.get_value("test_key") == ""
    # test setting to empty value (sensitive=True)
    params["sensitive"] = True
    result = nc_app._session.ocs("POST", f"{nc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == ""
    if class_to_test == NC_APP.appconfig_ex or nc_app.srv_version["major"] >= 32:
        assert bool(result["sensitive"]) is True
    assert class_to_test.get_value("test_key") == ""


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("class_to_test", (NC_APP_ASYNC.appconfig_ex, NC_APP_ASYNC.preferences_ex))
async def test_appcfg_sensitive_async(anc_app, class_to_test):
    await class_to_test.delete("test_key")
    await class_to_test.set_value("test_key", "123", sensitive=True)
    assert await class_to_test.get_value("test_key") == "123"
    assert (await class_to_test.get_values(["test_key"]))[0].value == "123"
    await class_to_test.delete("test_key")
    # next code tests `sensitive` value from the `AppAPI`
    params = {"configKey": "test_key", "configValue": "123"}
    result = await anc_app._session.ocs("POST", f"{anc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    if class_to_test == NC_APP_ASYNC.appconfig_ex or (await anc_app.srv_version)["major"] >= 32:
        assert not result["sensitive"]  # by default if sensitive value is unspecified it is False
    await class_to_test.delete("test_key")
    params["sensitive"] = True
    result = await anc_app._session.ocs("POST", f"{anc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == "123"
    if class_to_test == NC_APP_ASYNC.appconfig_ex or (await anc_app.srv_version)["major"] >= 32:
        assert bool(result["sensitive"]) is True
    params.pop("sensitive")  # if we not specify value, AppEcosystem should not change it.
    result = await anc_app._session.ocs("POST", f"{anc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == "123"
    if class_to_test == NC_APP_ASYNC.appconfig_ex or (await anc_app.srv_version)["major"] >= 32:
        assert bool(result["sensitive"]) is True
    params["sensitive"] = False
    result = await anc_app._session.ocs("POST", f"{anc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == "123"
    if class_to_test == NC_APP_ASYNC.appconfig_ex or (await anc_app.srv_version)["major"] >= 32:
        assert bool(result["sensitive"]) is False
    # test setting to empty value (sensitive=False)
    params["configValue"] = ""
    result = await anc_app._session.ocs("POST", f"{anc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == ""
    if class_to_test == NC_APP_ASYNC.appconfig_ex or (await anc_app.srv_version)["major"] >= 32:
        assert bool(result["sensitive"]) is False
    assert await class_to_test.get_value("test_key") == ""
    # test setting to empty value (sensitive=True)
    params["sensitive"] = True
    result = await anc_app._session.ocs("POST", f"{anc_app._session.ae_url}/{class_to_test._url_suffix}", json=params)
    assert result["configkey"] == "test_key"
    assert result["configvalue"] == ""
    if class_to_test == NC_APP_ASYNC.appconfig_ex or (await anc_app.srv_version)["major"] >= 32:
        assert bool(result["sensitive"]) is True
    assert await class_to_test.get_value("test_key") == ""
