import pytest

from nc_py_api import NextcloudException

from gfixture import NC_TO_TEST


TEST_USER_NAME = "test_cover_user"
TEST_USER_PASSWORD = "az1dcaNG4c42"


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_user(nc):
    admin = nc.users.get("admin")
    assert admin


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_user_404(nc):
    with pytest.raises(NextcloudException):
        nc.users.get("non existing user")


@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_create_user(nc):
    try:
        nc.users.delete(TEST_USER_NAME)
    except NextcloudException:
        pass
    nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    with pytest.raises(NextcloudException):
        nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)


@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_delete_user(nc):
    try:
        nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    except NextcloudException:
        pass
    nc.users.delete(TEST_USER_NAME)
    with pytest.raises(NextcloudException):
        nc.users.delete(TEST_USER_NAME)


@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_list_users(nc):
    try:
        nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    except NextcloudException:
        pass
    users = nc.users.list()
    assert "admin" in users
    users = nc.users.list(limit=1)
    assert len(users) == 1
    assert users[0] != nc.users.list(limit=1, offset=1)[0]
    users = nc.users.list(mask="test_cover_")
    assert len(users) == 1
    nc.users.delete(TEST_USER_NAME)


@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_enable_disable_user(nc):
    try:
        nc.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    except NextcloudException:
        pass
    nc.users.disable(TEST_USER_NAME)
    user = nc.users.get(TEST_USER_NAME)
    assert not user["enabled"]
    nc.users.enable(TEST_USER_NAME)
    user = nc.users.get(TEST_USER_NAME)
    assert user["enabled"]
    nc.users.delete(TEST_USER_NAME)
