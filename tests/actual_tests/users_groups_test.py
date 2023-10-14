import contextlib
from datetime import datetime, timezone
from os import environ

import pytest

from nc_py_api import NextcloudException


def test_group_get_list(nc, nc_client):
    groups = nc.users_groups.get_list()
    assert isinstance(groups, list)
    assert len(groups) >= 3
    assert environ["TEST_GROUP_BOTH"] in groups
    assert environ["TEST_GROUP_USER"] in groups
    groups = nc.users_groups.get_list(mask="test_nc_py_api_group")
    assert len(groups) == 2
    groups = nc.users_groups.get_list(limit=1)
    assert len(groups) == 1
    assert groups[0] != nc.users_groups.get_list(limit=1, offset=1)[0]


def test_group_get_details(nc, nc_client):
    groups = nc.users_groups.get_details(mask=environ["TEST_GROUP_BOTH"])
    assert len(groups) == 1
    group = groups[0]
    assert group.group_id == environ["TEST_GROUP_BOTH"]
    assert group.display_name == environ["TEST_GROUP_BOTH"]
    assert group.disabled is False
    assert isinstance(group.user_count, int)
    assert isinstance(group.can_add, bool)
    assert isinstance(group.can_remove, bool)
    assert str(group).find("user_count=") != -1


def test_get_non_existing_group(nc_client):
    groups = nc_client.users_groups.get_list(mask="Such group should not be present")
    assert isinstance(groups, list)
    assert not groups


def test_group_edit(nc_client):
    display_name = str(int(datetime.now(timezone.utc).timestamp()))
    nc_client.users_groups.edit(environ["TEST_GROUP_USER"], display_name=display_name)
    assert nc_client.users_groups.get_details(mask=environ["TEST_GROUP_USER"])[0].display_name == display_name
    with pytest.raises(NextcloudException) as exc_info:
        nc_client.users_groups.edit("non_existing_group", display_name="earth people")
    # remove 996 in the future, PR was already accepted in Nextcloud Server
    assert exc_info.value.status_code in (
        404,
        996,
    )


def test_group_display_name_promote_demote(nc_client):
    group_id = "test_group_display_name_promote_demote"
    with contextlib.suppress(NextcloudException):
        nc_client.users_groups.delete(group_id)
    nc_client.users_groups.create(group_id, display_name="12345")
    try:
        group_details = nc_client.users_groups.get_details(mask=group_id)
        assert len(group_details) == 1
        assert group_details[0].display_name == "12345"

        group_members = nc_client.users_groups.get_members(group_id)
        assert isinstance(group_members, list)
        assert not group_members
        group_subadmins = nc_client.users_groups.get_subadmins(group_id)
        assert isinstance(group_subadmins, list)
        assert not group_subadmins

        nc_client.users.add_to_group(environ["TEST_USER_ID"], group_id)
        group_members = nc_client.users_groups.get_members(group_id)
        assert group_members[0] == environ["TEST_USER_ID"]
        group_subadmins = nc_client.users_groups.get_subadmins(group_id)
        assert not group_subadmins
        nc_client.users.promote_to_subadmin(environ["TEST_USER_ID"], group_id)
        group_subadmins = nc_client.users_groups.get_subadmins(group_id)
        assert group_subadmins[0] == environ["TEST_USER_ID"]

        nc_client.users.demote_from_subadmin(environ["TEST_USER_ID"], group_id)
        group_subadmins = nc_client.users_groups.get_subadmins(group_id)
        assert not group_subadmins
        nc_client.users.remove_from_group(environ["TEST_USER_ID"], group_id)
        group_members = nc_client.users_groups.get_members(group_id)
        assert not group_members
    finally:
        nc_client.users_groups.delete(group_id)
        with pytest.raises(NextcloudException):
            nc_client.users_groups.delete(group_id)
