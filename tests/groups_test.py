import pytest

from nc_py_api import NextcloudException, Nextcloud

from gfixture import NC_TO_TEST

TEST_GROUP_NAME = "test_coverage_group"


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
@pytest.mark.parametrize("params", ((TEST_GROUP_NAME, ), (TEST_GROUP_NAME, "display name")))
def test_create_delete_group(nc, params):
    test_group_name = params[0]
    try:
        nc.users_groups.delete(test_group_name)
    except NextcloudException:
        pass
    nc.users_groups.create(*params)
    with pytest.raises(NextcloudException):
        nc.users_groups.create(*params)
    nc.users_groups.delete(test_group_name)
    with pytest.raises(NextcloudException):
        nc.users_groups.delete(test_group_name)


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_list_group(nc):
    try:
        nc.users_groups.create(TEST_GROUP_NAME)
    except NextcloudException:
        pass
    try:
        nc.users_groups.create(TEST_GROUP_NAME + "2")
    except NextcloudException:
        pass
    groups = nc.users_groups.list()
    assert len(groups) >= 2
    assert TEST_GROUP_NAME in groups
    assert TEST_GROUP_NAME + "2" in groups
    groups = nc.users_groups.list(mask=TEST_GROUP_NAME)
    assert len(groups) == 2
    groups = nc.users_groups.list(limit=1)
    assert len(groups) == 1
    assert groups[0] != nc.users_groups.list(limit=1, offset=1)[0]
    nc.users_groups.delete(TEST_GROUP_NAME)
    nc.users_groups.delete(TEST_GROUP_NAME + "2")


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_group_edit(nc):
    try:
        nc.users_groups.create(TEST_GROUP_NAME)
    except NextcloudException:
        pass
    nc.users_groups.edit(TEST_GROUP_NAME, display_name="earth people")
    nc.users_groups.delete(TEST_GROUP_NAME)
    with pytest.raises(NextcloudException) as exc_info:
        nc.users_groups.edit(TEST_GROUP_NAME, display_name="earth people")
    assert exc_info.value.status_code == 996


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_group_members_promote_demote(nc):
    try:
        nc.users_groups.create(TEST_GROUP_NAME)
    except NextcloudException:
        pass
    group_members = nc.users_groups.get_members(TEST_GROUP_NAME)
    assert not group_members
    group_subadmins = nc.users_groups.get_subadmins(TEST_GROUP_NAME)
    assert not group_subadmins
    try:
        try:
            nc.users.create("test_group_user", password="test_group_user")
        except NextcloudException:
            pass
        nc.users.add_to_group("test_group_user", TEST_GROUP_NAME)
        group_members = nc.users_groups.get_members(TEST_GROUP_NAME)
        assert group_members
        group_subadmins = nc.users_groups.get_subadmins(TEST_GROUP_NAME)
        assert not group_subadmins
        nc.users.promote_to_subadmin("test_group_user", TEST_GROUP_NAME)
        group_subadmins = nc.users_groups.get_subadmins(TEST_GROUP_NAME)
        assert group_subadmins
        nc.users.demote_from_subadmin("test_group_user", TEST_GROUP_NAME)
        group_subadmins = nc.users_groups.get_subadmins(TEST_GROUP_NAME)
        assert not group_subadmins
        nc.users.remove_from_group("test_group_user", TEST_GROUP_NAME)
        group_members = nc.users_groups.get_members(TEST_GROUP_NAME)
        assert not group_members
    finally:
        nc.users_groups.delete(TEST_GROUP_NAME)
        try:
            nc.users.delete("test_group_user")
        except NextcloudException:
            pass
