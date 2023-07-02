import pytest

from gfixture import NC_APP

from nc_py_api import NextcloudException, ApiScope


if NC_APP is None:
    pytest.skip("Only for Nextcloud App mode", allow_module_level=True)


def test_get_users_list():
    users = NC_APP.users_list()
    assert users
    assert NC_APP.user in users


def test_scope_allowed():
    for i in ApiScope:
        assert NC_APP.scope_allowed(i)
    assert not NC_APP.scope_allowed(0)
    assert not NC_APP.scope_allowed(999999999)


def test_change_user():
    orig_user = NC_APP.user
    try:
        orig_capabilities = NC_APP.capabilities
        assert NC_APP.users_status.get_current()
        NC_APP.user = ""
        with pytest.raises(NextcloudException) as exc_info:
            NC_APP.users_status.get_current()
        assert exc_info.value.status_code == 404
        assert orig_capabilities != NC_APP.capabilities
    finally:
        NC_APP.user = orig_user
    assert orig_capabilities == NC_APP.capabilities
