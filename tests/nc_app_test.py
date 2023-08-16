from os import environ

import pytest
from gfixture import NC, NC_APP

from nc_py_api.ex_app import ApiScope

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


def test_app_cfg():
    app_cfg = NC_APP.app_cfg
    assert app_cfg.app_name == environ["APP_ID"]
    assert app_cfg.app_version == environ["APP_VERSION"]
    assert app_cfg.app_secret == environ["APP_SECRET"].encode("UTF-8")


@pytest.mark.skipif(NC is None, reason="Usual Nextcloud mode required for the test")
def test_scope_allow_app_ecosystem_disabled():
    NC.apps.disable("app_ecosystem_v2")
    try:
        assert NC_APP.scope_allowed(ApiScope.FILES)
        NC_APP.update_server_info()
        assert not NC_APP.scope_allowed(ApiScope.FILES)
    finally:
        NC.apps.enable("app_ecosystem_v2")
        NC_APP.update_server_info()


def test_change_user():
    orig_user = NC_APP.user
    try:
        orig_capabilities = NC_APP.capabilities
        assert NC_APP.users.status.available
        NC_APP.user = ""
        assert not NC_APP.users.status.available
        assert orig_capabilities != NC_APP.capabilities
    finally:
        NC_APP.user = orig_user
    assert orig_capabilities == NC_APP.capabilities
