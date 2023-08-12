import contextlib

import pytest
from gfixture import NC_TO_TEST

from nc_py_api import Nextcloud, NextcloudException, NextcloudExceptionNotFound

TEST_USER_NAME = "test_cover_user"
TEST_USER_PASSWORD = "az1dcaNG4c42"


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_user_details(nc):
    admin = nc.users.get_details("admin")
    assert admin
    current_user = nc.users.get_details()
    assert current_user
    admin.pop("quota", None)  # `quota` is a little bit different
    current_user.pop("quota", None)
    assert admin == current_user


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_current_user_wo_user(nc):
    orig_user = nc._session.user
    try:
        nc._session.user = ""
        with pytest.raises(ValueError):
            nc.users.get_details()
    finally:
        nc._session.user = orig_user


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_user_404(nc):
    with pytest.raises(NextcloudException):
        nc.users.get_details("non existing user")


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_create_user(nc):
    with contextlib.suppress(NextcloudException):
        nc.users.delete(TEST_USER_NAME)
    nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    with pytest.raises(NextcloudException):
        nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    nc.users.delete(TEST_USER_NAME)


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_create_user_with_groups(nc):
    with contextlib.suppress(NextcloudException):
        nc.users.delete(TEST_USER_NAME)
    nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD, groups=["admin"])
    admin_group = nc.users.groups.get_members("admin")
    assert TEST_USER_NAME in admin_group
    nc.users.delete(TEST_USER_NAME)


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_create_user_no_name_mail(nc):
    with contextlib.suppress(NextcloudException):
        nc.users.delete(TEST_USER_NAME)
    with pytest.raises(ValueError):
        nc.users.create(TEST_USER_NAME)
    with pytest.raises(ValueError):
        nc.users.create(TEST_USER_NAME, password="")
    with pytest.raises(ValueError):
        nc.users.create(TEST_USER_NAME, email="")


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_delete_user(nc):
    with contextlib.suppress(NextcloudException):
        nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    nc.users.delete(TEST_USER_NAME)
    with pytest.raises(NextcloudExceptionNotFound):
        nc.users.delete(TEST_USER_NAME)


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_users_get_list(nc):
    with contextlib.suppress(NextcloudException):
        nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    users = nc.users.get_list()
    assert isinstance(users, list)
    assert "admin" in users
    users = nc.users.get_list(limit=1)
    assert len(users) == 1
    assert users[0] != nc.users.get_list(limit=1, offset=1)[0]
    users = nc.users.get_list(mask="test_cover_")
    assert len(users) == 1
    nc.users.delete(TEST_USER_NAME)


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_enable_disable_user(nc):
    with contextlib.suppress(NextcloudException):
        nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    nc.users.disable(TEST_USER_NAME)
    user = nc.users.get_details(TEST_USER_NAME)
    assert not user["enabled"]
    nc.users.enable(TEST_USER_NAME)
    user = nc.users.get_details(TEST_USER_NAME)
    assert user["enabled"]
    nc.users.delete(TEST_USER_NAME)


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_user_editable_fields(nc):
    editable_fields = nc.users.editable_fields()
    assert isinstance(editable_fields, list)
    assert editable_fields


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_edit_user(nc):
    nc.users.edit(nc.user, address="Le Pame")
    current_user = nc.users.get_details()
    assert current_user["address"] == "Le Pame"
    nc.users.edit(nc.user, address="", email="admin@gmx.net")
    current_user = nc.users.get_details()
    assert current_user["address"] == ""
    assert current_user["email"] == "admin@gmx.net"


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_resend_user_email(nc):
    nc.users.resend_welcome_email(nc.user)
