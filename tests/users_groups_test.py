import pytest
from gfixture import NC_APP, NC_TO_TEST

from nc_py_api import Nextcloud, NextcloudException, users_groups

TEST_GROUP_NAME = "test_coverage_group1"
TEST_GROUP_NAME2 = "test_coverage_group2"


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
@pytest.mark.parametrize("params", ((TEST_GROUP_NAME,), (TEST_GROUP_NAME, "display name")))
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
def test_group_get_list(nc):
    for i in (TEST_GROUP_NAME, TEST_GROUP_NAME2):
        try:
            nc.users_groups.create(i)
        except NextcloudException:
            pass
    groups = nc.users_groups.get_list()
    assert isinstance(groups, list)
    assert len(groups) >= 2
    assert TEST_GROUP_NAME in groups
    assert TEST_GROUP_NAME2 in groups
    groups = nc.users_groups.get_list(mask=TEST_GROUP_NAME)
    assert len(groups) == 1
    groups = nc.users_groups.get_list(limit=1)
    assert len(groups) == 1
    assert groups[0] != nc.users_groups.get_list(limit=1, offset=1)[0]
    nc.users_groups.delete(TEST_GROUP_NAME)
    nc.users_groups.delete(TEST_GROUP_NAME2)


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_get_non_existing_group(nc):
    groups = nc.users_groups.get_list(mask="Such group should not be present")
    assert isinstance(groups, list)
    assert not groups


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_group_get_details(nc):
    try:
        nc.users_groups.delete(TEST_GROUP_NAME)
    except NextcloudException:
        pass
    try:
        nc.users_groups.create(TEST_GROUP_NAME)
    except NextcloudException:
        pass
    groups = nc.users_groups.get_details(mask=TEST_GROUP_NAME)
    assert len(groups) == 1
    group = groups[0]
    assert group.group_id == TEST_GROUP_NAME
    assert group.display_name == TEST_GROUP_NAME
    assert not group.disabled
    assert isinstance(group.user_count, int)
    assert isinstance(group.can_add, bool)
    assert isinstance(group.can_remove, bool)
    nc.users_groups.delete(TEST_GROUP_NAME)


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_group_edit(nc):
    try:
        nc.users_groups.create(TEST_GROUP_NAME)
    except NextcloudException:
        pass
    nc.users_groups.edit(TEST_GROUP_NAME, display_name="earth people")
    assert nc.users_groups.get_details(mask=TEST_GROUP_NAME)[0].display_name == "earth people"
    nc.users_groups.delete(TEST_GROUP_NAME)
    with pytest.raises(NextcloudException) as exc_info:
        nc.users_groups.edit(TEST_GROUP_NAME, display_name="earth people")
    # remove 996 in the future, PR was already accepted in Nextcloud Server
    assert exc_info.value.status_code in (
        404,
        996,
    )


@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_group_members_promote_demote(nc):
    try:
        nc.users_groups.create(TEST_GROUP_NAME)
    except NextcloudException:
        pass
    group_members = nc.users_groups.get_members(TEST_GROUP_NAME)
    assert not group_members
    assert isinstance(group_members, list)
    group_subadmins = nc.users_groups.get_subadmins(TEST_GROUP_NAME)
    assert isinstance(group_subadmins, list)
    assert not group_subadmins
    try:
        try:
            nc.users.create("test_group_user", password="test_group_user")
        except NextcloudException:
            pass
        nc.users.add_to_group("test_group_user", TEST_GROUP_NAME)
        group_members = nc.users_groups.get_members(TEST_GROUP_NAME)
        assert group_members
        assert isinstance(group_members[0], str)
        group_subadmins = nc.users_groups.get_subadmins(TEST_GROUP_NAME)
        assert not group_subadmins
        nc.users.promote_to_subadmin("test_group_user", TEST_GROUP_NAME)
        group_subadmins = nc.users_groups.get_subadmins(TEST_GROUP_NAME)
        assert group_subadmins
        assert isinstance(group_subadmins[0], str)
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


@pytest.mark.skipif(NC_APP is None, reason="Test only for NextcloudApp.")
def test_app_mode():
    groups_list = NC_APP.users_groups.get_list()
    assert isinstance(groups_list, list)
    groups_detailed_list = NC_APP.users_groups.get_details()
    assert isinstance(groups_detailed_list, list)
    for i in groups_detailed_list:
        assert isinstance(i, users_groups.GroupDetails)
