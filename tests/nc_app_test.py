from os import environ

from nc_py_api.ex_app import ApiScope


def test_get_users_list(nc_app):
    users = nc_app.users_list()
    assert users
    assert nc_app.user in users


def test_scope_allowed(nc_app):
    for i in ApiScope:
        assert nc_app.scope_allowed(i)
    assert not nc_app.scope_allowed(0)  # noqa
    assert not nc_app.scope_allowed(999999999)  # noqa


def test_app_cfg(nc_app):
    app_cfg = nc_app.app_cfg
    assert app_cfg.app_name == environ["APP_ID"]
    assert app_cfg.app_version == environ["APP_VERSION"]
    assert app_cfg.app_secret == environ["APP_SECRET"].encode("UTF-8")


def test_scope_allow_app_ecosystem_disabled(nc_client, nc_app):
    assert nc_app.scope_allowed(ApiScope.FILES)
    nc_client.apps.disable("app_ecosystem_v2")
    try:
        assert nc_app.scope_allowed(ApiScope.FILES)
        nc_app.update_server_info()
        assert not nc_app.scope_allowed(ApiScope.FILES)
    finally:
        nc_client.apps.enable("app_ecosystem_v2")
        nc_app.update_server_info()


def test_change_user(nc_app):
    orig_user = nc_app.user
    try:
        orig_capabilities = nc_app.capabilities
        assert nc_app.user_status.available
        nc_app.user = ""
        assert not nc_app.user_status.available
        assert orig_capabilities != nc_app.capabilities
    finally:
        nc_app.user = orig_user
    assert orig_capabilities == nc_app.capabilities
