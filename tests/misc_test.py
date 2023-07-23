import pytest
from gfixture import NC_APP

from nc_py_api import NextcloudException, check_error, misc


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
    misc.require_capabilities("app_ecosystem_v2", NC_APP.capabilities)
    misc.require_capabilities(["app_ecosystem_v2", "theming"], NC_APP.capabilities)
    with pytest.raises(NextcloudException):
        misc.require_capabilities("non_exist_capability", NC_APP.capabilities)
    with pytest.raises(NextcloudException):
        misc.require_capabilities(["non_exist_capability", "app_ecosystem_v2"], NC_APP.capabilities)
    with pytest.raises(NextcloudException):
        misc.require_capabilities(
            ["non_exist_capability", "non_exist_capability2", "app_ecosystem_v2"], NC_APP.capabilities
        )
