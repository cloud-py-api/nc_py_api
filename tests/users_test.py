import contextlib

import pytest

from nc_py_api import NextcloudException, NextcloudExceptionNotFound

TEST_USER_NAME = "test_cover_user"
TEST_USER_PASSWORD = "az1dcaNG4c42"


def test_get_user_details(nc):
    admin = nc.users.get_details("admin")
    assert admin
    current_user = nc.users.get_details()
    assert current_user
    admin.pop("quota", None)  # `quota` is a little bit different
    current_user.pop("quota", None)
    assert admin == current_user


def test_get_current_user_wo_user(nc):
    orig_user = nc._session.user
    try:
        nc._session.user = ""
        with pytest.raises(ValueError):
            nc.users.get_details()
    finally:
        nc._session.user = orig_user


def test_get_user_404(nc):
    with pytest.raises(NextcloudException):
        nc.users.get_details("non existing user")


def test_create_user(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users.delete(TEST_USER_NAME)
    nc_client.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    with pytest.raises(NextcloudException):
        nc_client.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    nc_client.users.delete(TEST_USER_NAME)


def test_create_user_with_groups(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users.delete(TEST_USER_NAME)
    nc_client.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD, groups=["admin"])
    admin_group = nc_client.users_groups.get_members("admin")
    assert TEST_USER_NAME in admin_group
    nc_client.users.delete(TEST_USER_NAME)


def test_create_user_no_name_mail(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users.delete(TEST_USER_NAME)
    with pytest.raises(ValueError):
        nc_client.users.create(TEST_USER_NAME)
    with pytest.raises(ValueError):
        nc_client.users.create(TEST_USER_NAME, password="")
    with pytest.raises(ValueError):
        nc_client.users.create(TEST_USER_NAME, email="")


def test_delete_user(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    nc_client.users.delete(TEST_USER_NAME)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_client.users.delete(TEST_USER_NAME)


def test_users_get_list(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    users = nc_client.users.get_list()
    assert isinstance(users, list)
    assert "admin" in users
    users = nc_client.users.get_list(limit=1)
    assert len(users) == 1
    assert users[0] != nc_client.users.get_list(limit=1, offset=1)[0]
    users = nc_client.users.get_list(mask="test_cover_")
    assert len(users) == 1
    nc_client.users.delete(TEST_USER_NAME)


def test_enable_disable_user(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    nc_client.users.disable(TEST_USER_NAME)
    user = nc_client.users.get_details(TEST_USER_NAME)
    assert not user["enabled"]
    nc_client.users.enable(TEST_USER_NAME)
    user = nc_client.users.get_details(TEST_USER_NAME)
    assert user["enabled"]
    nc_client.users.delete(TEST_USER_NAME)


def test_user_editable_fields(nc_client):
    editable_fields = nc_client.users.editable_fields()
    assert isinstance(editable_fields, list)
    assert editable_fields


def test_edit_user(nc_client):
    nc_client.users.edit(nc_client.user, address="Le Pame")
    current_user = nc_client.users.get_details()
    assert current_user["address"] == "Le Pame"
    nc_client.users.edit(nc_client.user, address="", email="admin@gmx.net")
    current_user = nc_client.users.get_details()
    assert current_user["address"] == ""
    assert current_user["email"] == "admin@gmx.net"


def test_resend_user_email(nc_client):
    nc_client.users.resend_welcome_email(nc_client.user)
