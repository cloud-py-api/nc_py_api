import datetime
import os

import pytest
from httpx import Request, Response

from nc_py_api import (
    AsyncNextcloud,
    AsyncNextcloudApp,
    Nextcloud,
    NextcloudApp,
    NextcloudException,
    ex_app,
)
from nc_py_api._deffered_error import DeferredError  # noqa
from nc_py_api._exceptions import check_error  # noqa
from nc_py_api._misc import nc_iso_time_to_datetime, require_capabilities  # noqa
from nc_py_api._session import BasicConfig  # noqa


@pytest.mark.parametrize("code", (995, 996, 997, 998, 999, 1000))
def test_check_error(code):
    if 996 <= code <= 999:
        with pytest.raises(NextcloudException):
            check_error(Response(code, request=Request(method="GET", url="https://example")))
    else:
        check_error(Response(code, request=Request(method="GET", url="https://example")))


def test_nc_exception_to_str():
    reason = "this is a reason"
    info = "some info"
    try:
        raise NextcloudException(status_code=666, reason=reason, info=info)
    except NextcloudException as e:
        assert str(e) == f"[666] {reason} <{info}>"


def test_require_capabilities(nc_app):
    require_capabilities("app_api", nc_app.capabilities)
    require_capabilities(["app_api", "theming"], nc_app.capabilities)
    with pytest.raises(NextcloudException):
        require_capabilities("non_exist_capability", nc_app.capabilities)
    with pytest.raises(NextcloudException):
        require_capabilities(["non_exist_capability", "app_api"], nc_app.capabilities)
    with pytest.raises(NextcloudException):
        require_capabilities(["non_exist_capability", "non_exist_capability2", "app_api"], nc_app.capabilities)
    with pytest.raises(NextcloudException):
        require_capabilities("app_api.non_exist_capability", nc_app.capabilities)


def test_config_get_value():
    BasicConfig()._get_config_value("non_exist_value", raise_not_found=False)
    with pytest.raises(ValueError):
        BasicConfig()._get_config_value("non_exist_value")
    assert BasicConfig()._get_config_value("non_exist_value", non_exist_value=123) == 123


def test_deffered_error():
    try:
        import unknown_non_exist_module
    except ImportError as ex:
        unknown_non_exist_module = DeferredError(ex)

    with pytest.raises(ModuleNotFoundError):
        unknown_non_exist_module.some_class_or_func()


def test_response_headers(nc):
    old_headers = nc.response_headers
    nc.users.get_user(nc.user)  # do not remove "nc.user" arguments, it helps to trigger response header updates.
    assert old_headers != nc.response_headers


@pytest.mark.asyncio(scope="session")
async def test_response_headers_async(anc):
    old_headers = anc.response_headers
    await anc.users.get_user(await anc.user)
    assert old_headers != anc.response_headers


def test_nc_iso_time_to_datetime():
    parsed_time = nc_iso_time_to_datetime("invalid")
    assert parsed_time == datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


def test_persist_transformers_cache(nc_app):
    assert "TRANSFORMERS_CACHE" not in os.environ
    from nc_py_api.ex_app import persist_transformers_cache  # noqa

    assert os.environ["TRANSFORMERS_CACHE"]
    os.environ.pop("TRANSFORMERS_CACHE")


def test_verify_version(nc_app):
    version_file_path = os.path.join(ex_app.persistent_storage(), "_version.info")
    if os.path.exists(version_file_path):
        os.remove(version_file_path)
    r = ex_app.verify_version(False)
    assert not os.path.getsize(version_file_path)
    assert isinstance(r, tuple)
    assert r[0] == ""
    assert r[1] == os.environ["APP_VERSION"]
    r = ex_app.verify_version(True)
    assert os.path.getsize(version_file_path)
    assert r[0] == ""
    assert r[1] == os.environ["APP_VERSION"]
    assert ex_app.verify_version() is None


def test_init_adapter_dav(nc_any):
    new_nc = Nextcloud() if isinstance(nc_any, Nextcloud) else NextcloudApp()
    new_nc._session.init_adapter_dav()
    old_adapter = getattr(new_nc._session, "adapter_dav", None)
    assert old_adapter is not None
    new_nc._session.init_adapter_dav()
    assert old_adapter == getattr(new_nc._session, "adapter_dav", None)
    new_nc._session.init_adapter_dav(restart=True)
    assert old_adapter != getattr(new_nc._session, "adapter_dav", None)


@pytest.mark.asyncio(scope="session")
async def test_init_adapter_dav_async(anc_any):
    new_nc = AsyncNextcloud() if isinstance(anc_any, AsyncNextcloud) else AsyncNextcloudApp()
    new_nc._session.init_adapter_dav()
    old_adapter = getattr(new_nc._session, "adapter_dav", None)
    assert old_adapter is not None
    new_nc._session.init_adapter_dav()
    assert old_adapter == getattr(new_nc._session, "adapter_dav", None)
    new_nc._session.init_adapter_dav(restart=True)
    assert old_adapter != getattr(new_nc._session, "adapter_dav", None)


def test_no_initial_connection(nc_any):
    new_nc = Nextcloud() if isinstance(nc_any, Nextcloud) else NextcloudApp()
    assert not new_nc._session._capabilities
    _ = new_nc.srv_version
    assert new_nc._session._capabilities


@pytest.mark.asyncio(scope="session")
async def test_no_initial_connection_async(anc_any):
    new_nc = AsyncNextcloud() if isinstance(anc_any, AsyncNextcloud) else AsyncNextcloudApp()
    assert not new_nc._session._capabilities
    _ = await new_nc.srv_version
    assert new_nc._session._capabilities


def test_ocs_timeout(nc_any):
    new_nc = Nextcloud(npa_timeout=0.01) if isinstance(nc_any, Nextcloud) else NextcloudApp(npa_timeout=0.01)
    with pytest.raises(NextcloudException) as e:
        if new_nc.weather_status.set_location(latitude=41.896655, longitude=12.488776):
            new_nc.weather_status.get_forecast()
    if e.value.status_code in (500, 996):
        pytest.skip("Some network problem on the host")
    assert e.value.status_code == 408


@pytest.mark.asyncio(scope="session")
async def test_ocs_timeout_async(anc_any):
    new_nc = (
        AsyncNextcloud(npa_timeout=0.01) if isinstance(anc_any, AsyncNextcloud) else AsyncNextcloudApp(npa_timeout=0.01)
    )
    with pytest.raises(NextcloudException) as e:
        if await new_nc.weather_status.set_location(latitude=41.896655, longitude=12.488776):
            await new_nc.weather_status.get_forecast()
    if e.value.status_code in (500, 996):
        pytest.skip("Some network problem on the host")
    assert e.value.status_code == 408


def test_public_ocs(nc_any):
    r = nc_any.ocs("GET", "/ocs/v1.php/cloud/capabilities")
    assert r == nc_any.ocs("GET", "ocs/v1.php/cloud/capabilities")
    assert r == nc_any._session.ocs("GET", "ocs/v1.php/cloud/capabilities")  # noqa


@pytest.mark.asyncio(scope="session")
async def test_public_ocs_async(anc_any):
    r = await anc_any.ocs("GET", "/ocs/v1.php/cloud/capabilities")
    assert r == await anc_any.ocs("GET", "ocs/v1.php/cloud/capabilities")
    assert r == await anc_any._session.ocs("GET", "ocs/v1.php/cloud/capabilities")  # noqa


def test_perform_login(nc_any):
    new_nc = Nextcloud() if isinstance(nc_any, Nextcloud) else NextcloudApp()
    assert not new_nc._session._capabilities
    new_nc.perform_login()
    assert new_nc._session._capabilities


@pytest.mark.asyncio(scope="session")
async def test_perform_login_async(anc_any):
    new_nc = AsyncNextcloud() if isinstance(anc_any, Nextcloud) else AsyncNextcloudApp()
    assert not new_nc._session._capabilities
    await new_nc.perform_login()
    assert new_nc._session._capabilities
