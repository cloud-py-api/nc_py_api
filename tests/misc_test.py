import pytest
from gfixture import NC_APP, NC_TO_TEST

from nc_py_api import NextcloudException
from nc_py_api._deffered_error import DeferredError  # noqa
from nc_py_api._exceptions import check_error  # noqa
from nc_py_api._misc import require_capabilities  # noqa
from nc_py_api._session import BasicConfig  # noqa


@pytest.mark.parametrize("code", (995, 996, 997, 998, 999, 1000))
def test_check_error(code):
    if 996 <= code <= 999:
        with pytest.raises(NextcloudException):
            check_error(code)
    else:
        check_error(code)


def test_nc_exception_to_str():
    reason = "this is a reason"
    info = "some info"
    try:
        raise NextcloudException(status_code=666, reason=reason, info=info)
    except NextcloudException as e:
        assert str(e) == f"[666] {reason} <{info}>"


@pytest.mark.skipif(NC_APP is None, reason="Test assumes the AppEcosystem is installed")
def test_require_capabilities():
    require_capabilities("app_ecosystem_v2", NC_APP.capabilities)
    require_capabilities(["app_ecosystem_v2", "theming"], NC_APP.capabilities)
    with pytest.raises(NextcloudException):
        require_capabilities("non_exist_capability", NC_APP.capabilities)
    with pytest.raises(NextcloudException):
        require_capabilities(["non_exist_capability", "app_ecosystem_v2"], NC_APP.capabilities)
    with pytest.raises(NextcloudException):
        require_capabilities(["non_exist_capability", "non_exist_capability2", "app_ecosystem_v2"], NC_APP.capabilities)


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


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_ocs_response_headers(nc):
    old_headers = nc.response_headers
    nc.users.get_details()
    assert old_headers != nc.response_headers
