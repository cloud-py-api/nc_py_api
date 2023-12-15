import contextlib
import datetime
from io import BytesIO
from os import environ

import pytest
from PIL import Image

from nc_py_api import (
    AsyncNextcloudApp,
    NextcloudApp,
    NextcloudException,
    NextcloudExceptionNotFound,
    users,
)


def _test_get_user_info(admin: users.UserInfo, current_user: users.UserInfo):
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


def test_get_user_info(nc):
    admin = nc.users.get_user("admin")
    current_user = nc.users.get_user()
    _test_get_user_info(admin, current_user)


@pytest.mark.asyncio(scope="session")
async def test_get_user_info_async(anc):
    admin = await anc.users.get_user("admin")
    current_user = await anc.users.get_user()
    _test_get_user_info(admin, current_user)


def test_get_current_user_wo_user(nc):
    orig_user = nc._session.user
    try:
        nc._session.set_user("")
        if isinstance(nc, NextcloudApp):
            with pytest.raises(NextcloudException):
                nc.users.get_user()
        else:
            assert isinstance(nc.users.get_user(), users.UserInfo)
    finally:
        nc._session.set_user(orig_user)


@pytest.mark.asyncio(scope="session")
async def test_get_current_user_wo_user_async(anc):
    orig_user = await anc._session.user
    try:
        anc._session.set_user("")
        if isinstance(anc, AsyncNextcloudApp):
            with pytest.raises(NextcloudException):
                await anc.users.get_user()
        else:
            assert isinstance(await anc.users.get_user(), users.UserInfo)
    finally:
        anc._session.set_user(orig_user)


def test_get_user_404(nc):
    with pytest.raises(NextcloudException):
        nc.users.get_user("non existing user")


@pytest.mark.asyncio(scope="session")
async def test_get_user_404_async(anc):
    with pytest.raises(NextcloudException):
        await anc.users.get_user("non existing user")


def test_create_user_with_groups(nc_client):
    admin_group = nc_client.users_groups.get_members("admin")
    assert environ["TEST_ADMIN_ID"] in admin_group
    assert environ["TEST_USER_ID"] not in admin_group


@pytest.mark.asyncio(scope="session")
async def test_create_user_with_groups_async(anc_client):
    admin_group = await anc_client.users_groups.get_members("admin")
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


@pytest.mark.asyncio(scope="session")
async def test_create_user_no_name_mail_async(anc_client):
    test_user_name = "test_create_user_no_name_mail"
    with contextlib.suppress(NextcloudException):
        await anc_client.users.delete(test_user_name)
    with pytest.raises(ValueError):
        await anc_client.users.create(test_user_name)
    with pytest.raises(ValueError):
        await anc_client.users.create(test_user_name, password="")
    with pytest.raises(ValueError):
        await anc_client.users.create(test_user_name, email="")


def test_delete_user(nc_client):
    test_user_name = "test_delete_user"
    with contextlib.suppress(NextcloudException):
        nc_client.users.create(test_user_name, password="az1dcaNG4c42")
    nc_client.users.delete(test_user_name)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_client.users.delete(test_user_name)


@pytest.mark.asyncio(scope="session")
async def test_delete_user_async(anc_client):
    test_user_name = "test_delete_user"
    with contextlib.suppress(NextcloudException):
        await anc_client.users.create(test_user_name, password="az1dcaNG4c42")
    await anc_client.users.delete(test_user_name)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_client.users.delete(test_user_name)


def test_users_get_list(nc, nc_client):
    _users = nc.users.get_list()
    assert isinstance(_users, list)
    assert nc.user in _users
    assert environ["TEST_ADMIN_ID"] in _users
    assert environ["TEST_USER_ID"] in _users
    _users = nc.users.get_list(limit=1)
    assert len(_users) == 1
    assert _users[0] != nc.users.get_list(limit=1, offset=1)[0]
    _users = nc.users.get_list(mask=environ["TEST_ADMIN_ID"])
    assert len(_users) == 1


@pytest.mark.asyncio(scope="session")
async def test_users_get_list_async(anc, anc_client):
    _users = await anc.users.get_list()
    assert isinstance(_users, list)
    assert await anc.user in _users
    assert environ["TEST_ADMIN_ID"] in _users
    assert environ["TEST_USER_ID"] in _users
    _users = await anc.users.get_list(limit=1)
    assert len(_users) == 1
    assert _users[0] != (await anc.users.get_list(limit=1, offset=1))[0]
    _users = await anc.users.get_list(mask=environ["TEST_ADMIN_ID"])
    assert len(_users) == 1


def test_enable_disable_user(nc_client):
    test_user_name = "test_enable_disable_user"
    with contextlib.suppress(NextcloudException):
        nc_client.users.create(test_user_name, password="az1dcaNG4c42")
    nc_client.users.disable(test_user_name)
    assert nc_client.users.get_user(test_user_name).enabled is False
    nc_client.users.enable(test_user_name)
    assert nc_client.users.get_user(test_user_name).enabled is True
    nc_client.users.delete(test_user_name)


@pytest.mark.asyncio(scope="session")
async def test_enable_disable_user_async(anc_client):
    test_user_name = "test_enable_disable_user"
    with contextlib.suppress(NextcloudException):
        await anc_client.users.create(test_user_name, password="az1dcaNG4c42")
    await anc_client.users.disable(test_user_name)
    assert (await anc_client.users.get_user(test_user_name)).enabled is False
    await anc_client.users.enable(test_user_name)
    assert (await anc_client.users.get_user(test_user_name)).enabled is True
    await anc_client.users.delete(test_user_name)


def test_user_editable_fields(nc):
    editable_fields = nc.users.editable_fields()
    assert isinstance(editable_fields, list)
    assert editable_fields


@pytest.mark.asyncio(scope="session")
async def test_user_editable_fields_async(anc):
    editable_fields = await anc.users.editable_fields()
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


@pytest.mark.asyncio(scope="session")
async def test_edit_user_async(anc_client):
    await anc_client.users.edit(await anc_client.user, address="Le Pame", email="admino@gmx.net")
    current_user = await anc_client.users.get_user()
    assert current_user.address == "Le Pame"
    assert current_user.email == "admino@gmx.net"
    await anc_client.users.edit(await anc_client.user, address="", email="admin@gmx.net")
    current_user = await anc_client.users.get_user()
    assert current_user.address == ""
    assert current_user.email == "admin@gmx.net"


def test_resend_user_email(nc_client):
    nc_client.users.resend_welcome_email(nc_client.user)


@pytest.mark.asyncio(scope="session")
async def test_resend_user_email_async(anc_client):
    await anc_client.users.resend_welcome_email(await anc_client.user)


def test_avatars(nc):
    im = nc.users.get_avatar()
    im_64 = nc.users.get_avatar(size=64)
    im_black = nc.users.get_avatar(dark=True)
    im_64_black = nc.users.get_avatar(size=64, dark=True)
    assert len(im_64) < len(im)
    assert len(im_64_black) < len(im_black)
    for i in (im, im_64, im_black, im_64_black):
        img = Image.open(BytesIO(i))
        img.load()
    with pytest.raises(NextcloudException):
        nc.users.get_avatar("not_existing_user")


@pytest.mark.asyncio(scope="session")
async def test_avatars_async(anc):
    im = await anc.users.get_avatar()
    im_64 = await anc.users.get_avatar(size=64)
    im_black = await anc.users.get_avatar(dark=True)
    im_64_black = await anc.users.get_avatar(size=64, dark=True)
    assert len(im_64) < len(im)
    assert len(im_64_black) < len(im_black)
    for i in (im, im_64, im_black, im_64_black):
        img = Image.open(BytesIO(i))
        img.load()
    with pytest.raises(NextcloudException):
        await anc.users.get_avatar("not_existing_user")
