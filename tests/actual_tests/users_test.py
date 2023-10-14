import contextlib
import datetime
from os import environ

import pytest

from nc_py_api import (
    NextcloudApp,
    NextcloudException,
    NextcloudExceptionNotFound,
    users,
)


def test_get_user_info(nc):
    admin = nc.users.get_user("admin")
    current_user = nc.users.get_user()
    for i in (
        "user_id",
        "email",
        "display_name",
        "storage_location",
        "backend",
        "manager",
        "phone",
        "address",
        "website",
        "twitter",
        "fediverse",
        "organisation",
        "role",
        "headline",
        "biography",
        "language",
        "locale",
        "notify_email",
    ):
        assert getattr(current_user, i) == getattr(admin, i)
        assert isinstance(getattr(current_user, i), str)
        assert isinstance(getattr(admin, i), str)
    assert admin.enabled is True
    assert admin.enabled == current_user.enabled
    assert admin.profile_enabled is True
    assert admin.profile_enabled == current_user.profile_enabled
    assert isinstance(admin.last_login, datetime.datetime)
    assert isinstance(current_user.last_login, datetime.datetime)
    assert isinstance(admin.subadmin, list)
    assert isinstance(admin.quota, dict)
    assert isinstance(admin.additional_mail, list)
    assert isinstance(admin.groups, list)
    assert isinstance(admin.backend_capabilities, dict)
    assert admin.display_name == "admin"
    assert str(admin).find("last_login=") != -1


def test_get_current_user_wo_user(nc):
    orig_user = nc._session.user
    try:
        nc._session.user = ""
        if isinstance(nc, NextcloudApp):
            with pytest.raises(NextcloudException):
                nc.users.get_user()
        else:
            assert isinstance(nc.users.get_user(), users.UserInfo)
    finally:
        nc._session.user = orig_user


def test_get_user_404(nc):
    with pytest.raises(NextcloudException):
        nc.users.get_user("non existing user")


def test_create_user_with_groups(nc_client):
    admin_group = nc_client.users_groups.get_members("admin")
    assert environ["TEST_ADMIN_ID"] in admin_group
    assert environ["TEST_USER_ID"] not in admin_group


def test_create_user_no_name_mail(nc_client):
    test_user_name = "test_create_user_no_name_mail"
    with contextlib.suppress(NextcloudException):
        nc_client.users.delete(test_user_name)
    with pytest.raises(ValueError):
        nc_client.users.create(test_user_name)
    with pytest.raises(ValueError):
        nc_client.users.create(test_user_name, password="")
    with pytest.raises(ValueError):
        nc_client.users.create(test_user_name, email="")


def test_delete_user(nc_client):
    test_user_name = "test_delete_user"
    with contextlib.suppress(NextcloudException):
        nc_client.users.create(test_user_name, password="az1dcaNG4c42")
    nc_client.users.delete(test_user_name)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_client.users.delete(test_user_name)


def test_users_get_list(nc, nc_client):
    users = nc.users.get_list()
    assert isinstance(users, list)
    assert nc.user in users
    assert environ["TEST_ADMIN_ID"] in users
    assert environ["TEST_USER_ID"] in users
    users = nc.users.get_list(limit=1)
    assert len(users) == 1
    assert users[0] != nc.users.get_list(limit=1, offset=1)[0]
    users = nc.users.get_list(mask=environ["TEST_ADMIN_ID"])
    assert len(users) == 1


def test_enable_disable_user(nc_client):
    test_user_name = "test_enable_disable_user"
    with contextlib.suppress(NextcloudException):
        nc_client.users.create(test_user_name, password="az1dcaNG4c42")
    nc_client.users.disable(test_user_name)
    assert nc_client.users.get_user(test_user_name).enabled is False
    nc_client.users.enable(test_user_name)
    assert nc_client.users.get_user(test_user_name).enabled is True
    nc_client.users.delete(test_user_name)


def test_user_editable_fields(nc):
    editable_fields = nc.users.editable_fields()
    assert isinstance(editable_fields, list)
    assert editable_fields


def test_edit_user(nc_client):
    nc_client.users.edit(nc_client.user, address="Le Pame", email="admino@gmx.net")
    current_user = nc_client.users.get_user()
    assert current_user.address == "Le Pame"
    assert current_user.email == "admino@gmx.net"
    nc_client.users.edit(nc_client.user, address="", email="admin@gmx.net")
    current_user = nc_client.users.get_user()
    assert current_user.address == ""
    assert current_user.email == "admin@gmx.net"


def test_resend_user_email(nc_client):
    nc_client.users.resend_welcome_email(nc_client.user)
