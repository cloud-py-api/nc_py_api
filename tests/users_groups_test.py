import contextlib

import pytest

from nc_py_api import NextcloudException, users_groups

TEST_GROUP_NAME = "test_coverage_group1"
TEST_GROUP_NAME2 = "test_coverage_group2"


@pytest.mark.parametrize("params", ((TEST_GROUP_NAME,), (TEST_GROUP_NAME, "display name")))
def test_create_delete_group(nc_client, params):
    test_group_name = params[0]
    with contextlib.suppress(NextcloudException):
        nc_client.users_groups.delete(test_group_name)
    nc_client.users_groups.create(*params)
    with pytest.raises(NextcloudException):
        nc_client.users_groups.create(*params)
    nc_client.users_groups.delete(test_group_name)
    with pytest.raises(NextcloudException):
        nc_client.users_groups.delete(test_group_name)


def test_group_get_list(nc_client):
    for i in (TEST_GROUP_NAME, TEST_GROUP_NAME2):
        with contextlib.suppress(NextcloudException):
            nc_client.users_groups.create(i)
    groups = nc_client.users_groups.get_list()
    assert isinstance(groups, list)
    assert len(groups) >= 2
    assert TEST_GROUP_NAME in groups
    assert TEST_GROUP_NAME2 in groups
    groups = nc_client.users_groups.get_list(mask=TEST_GROUP_NAME)
    assert len(groups) == 1
    groups = nc_client.users_groups.get_list(limit=1)
    assert len(groups) == 1
    assert groups[0] != nc_client.users_groups.get_list(limit=1, offset=1)[0]
    nc_client.users_groups.delete(TEST_GROUP_NAME)
    nc_client.users_groups.delete(TEST_GROUP_NAME2)


def test_get_non_existing_group(nc_client):
    groups = nc_client.users_groups.get_list(mask="Such group should not be present")
    assert isinstance(groups, list)
    assert not groups


def test_group_get_details(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users_groups.delete(TEST_GROUP_NAME)
    with contextlib.suppress(NextcloudException):
        nc_client.users_groups.create(TEST_GROUP_NAME)
    groups = nc_client.users_groups.get_details(mask=TEST_GROUP_NAME)
    assert len(groups) == 1
    group = groups[0]
    assert group.group_id == TEST_GROUP_NAME
    assert group.display_name == TEST_GROUP_NAME
    assert not group.disabled
    assert isinstance(group.user_count, int)
    assert isinstance(group.can_add, bool)
    assert isinstance(group.can_remove, bool)
    nc_client.users_groups.delete(TEST_GROUP_NAME)


def test_group_edit(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users_groups.create(TEST_GROUP_NAME)
    nc_client.users_groups.edit(TEST_GROUP_NAME, display_name="earth people")
    assert nc_client.users_groups.get_details(mask=TEST_GROUP_NAME)[0].display_name == "earth people"
    nc_client.users_groups.delete(TEST_GROUP_NAME)
    with pytest.raises(NextcloudException) as exc_info:
        nc_client.users_groups.edit(TEST_GROUP_NAME, display_name="earth people")
    # remove 996 in the future, PR was already accepted in Nextcloud Server
    assert exc_info.value.status_code in (
        404,
        996,
    )


def test_group_members_promote_demote(nc_client):
    with contextlib.suppress(NextcloudException):
        nc_client.users_groups.create(TEST_GROUP_NAME)
    group_members = nc_client.users_groups.get_members(TEST_GROUP_NAME)
    assert not group_members
    assert isinstance(group_members, list)
    group_subadmins = nc_client.users_groups.get_subadmins(TEST_GROUP_NAME)
    assert isinstance(group_subadmins, list)
    assert not group_subadmins
    try:
        with contextlib.suppress(NextcloudException):
            nc_client.users.create("test_group_user", password="test_group_user")
        nc_client.users.add_to_group("test_group_user", TEST_GROUP_NAME)
        group_members = nc_client.users_groups.get_members(TEST_GROUP_NAME)
        assert group_members
        assert isinstance(group_members[0], str)
        group_subadmins = nc_client.users_groups.get_subadmins(TEST_GROUP_NAME)
        assert not group_subadmins
        nc_client.users.promote_to_subadmin("test_group_user", TEST_GROUP_NAME)
        group_subadmins = nc_client.users_groups.get_subadmins(TEST_GROUP_NAME)
        assert group_subadmins
        assert isinstance(group_subadmins[0], str)
        nc_client.users.demote_from_subadmin("test_group_user", TEST_GROUP_NAME)
        group_subadmins = nc_client.users_groups.get_subadmins(TEST_GROUP_NAME)
        assert not group_subadmins
        nc_client.users.remove_from_group("test_group_user", TEST_GROUP_NAME)
        group_members = nc_client.users_groups.get_members(TEST_GROUP_NAME)
        assert not group_members
    finally:
        nc_client.users_groups.delete(TEST_GROUP_NAME)
        with contextlib.suppress(NextcloudException):
            nc_client.users.delete("test_group_user")


def test_app_mode(nc_app):
    groups_list = nc_app.users_groups.get_list()
    assert isinstance(groups_list, list)
    groups_detailed_list = nc_app.users_groups.get_details()
    assert isinstance(groups_detailed_list, list)
    for i in groups_detailed_list:
        assert isinstance(i, users_groups.GroupDetails)
