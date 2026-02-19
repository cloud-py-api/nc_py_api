import contextlib
from os import environ

import pytest

from nc_py_api import NextcloudException
from nc_py_api.teams import Circle, CircleConfig, Member, MemberLevel, MemberType


@pytest.mark.asyncio(scope="session")
async def test_teams_available(anc):
    assert await anc.teams.available


@pytest.mark.asyncio(scope="session")
async def test_teams_create_destroy(anc):
    circle = await anc.teams.create("test_nc_py_api_team_cd")
    try:
        assert isinstance(circle, Circle)
        assert circle.circle_id
        assert circle.name == "test_nc_py_api_team_cd"
        assert circle.display_name
        assert isinstance(circle.config, CircleConfig)
        assert isinstance(circle.population, int)
        assert isinstance(circle.description, str)
        assert isinstance(circle.url, str)
        assert isinstance(circle.creation, int)
        assert repr(circle).startswith("<Circle")
    finally:
        await anc.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_get_list(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_list")
    try:
        circles = await anc_any.teams.get_list()
        assert isinstance(circles, list)
        assert any(c.name == "test_nc_py_api_team_list" for c in circles)
        for c in circles:
            assert isinstance(c, Circle)
    finally:
        await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_get_details(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_det")
    try:
        details = await anc_any.teams.get_details(circle.circle_id)
        assert isinstance(details, Circle)
        assert details.circle_id == circle.circle_id
        assert details.name == "test_nc_py_api_team_det"
        assert isinstance(details.sanitized_name, str)
    finally:
        await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_edit_name(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_en")
    try:
        updated = await anc_any.teams.edit_name(circle.circle_id, "test_nc_py_api_team_en_new")
        assert isinstance(updated, Circle)
        assert updated.name == "test_nc_py_api_team_en_new"
        details = await anc_any.teams.get_details(circle.circle_id)
        assert details.name == "test_nc_py_api_team_en_new"
    finally:
        await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_edit_description(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_ed")
    try:
        updated = await anc_any.teams.edit_description(circle.circle_id, "Test description")
        assert isinstance(updated, Circle)
        assert updated.description == "Test description"
        details = await anc_any.teams.get_details(circle.circle_id)
        assert details.description == "Test description"
    finally:
        await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_edit_config(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_ec")
    try:
        new_config = CircleConfig.VISIBLE | CircleConfig.OPEN
        updated = await anc_any.teams.edit_config(circle.circle_id, int(new_config))
        assert isinstance(updated, Circle)
        assert updated.config & CircleConfig.VISIBLE
        assert updated.config & CircleConfig.OPEN
    finally:
        await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_owner(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_ow")
    try:
        details = await anc_any.teams.get_details(circle.circle_id)
        assert details.owner is not None
        assert isinstance(details.owner, Member)
        assert details.owner.user_id == "admin"
        assert details.owner.level == MemberLevel.OWNER
        assert details.initiator is not None
        assert isinstance(details.initiator, Member)
    finally:
        await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_members_add_remove(anc_any):
    test_user_id = environ.get("TEST_USER_ID", "")
    if not test_user_id:
        pytest.skip("No test user available")
    circle = await anc_any.teams.create("test_nc_py_api_team_mar")
    try:
        members = await anc_any.teams.get_members(circle.circle_id)
        assert isinstance(members, list)

        added = await anc_any.teams.add_member(circle.circle_id, test_user_id, MemberType.USER)
        assert isinstance(added, list)
        for m in added:
            assert isinstance(m, Member)

        members = await anc_any.teams.get_members(circle.circle_id)
        user_ids = [m.user_id for m in members]
        assert test_user_id in user_ids

        member = next(m for m in members if m.user_id == test_user_id)
        assert isinstance(member.member_id, str)
        assert member.member_id
        assert isinstance(member.user_type, MemberType)
        assert isinstance(member.level, MemberLevel)
        assert isinstance(member.status, str)
        assert isinstance(member.display_name, str)
        assert isinstance(member.single_id, str)
        assert isinstance(member.circle_id, str)
        assert repr(member).startswith("<Member")

        remaining = await anc_any.teams.remove_member(circle.circle_id, member.member_id)
        assert isinstance(remaining, list)
        user_ids = [m.user_id for m in remaining]
        assert test_user_id not in user_ids
    finally:
        await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_add_members_multi(anc_any):
    test_user_id = environ.get("TEST_USER_ID", "")
    test_admin_id = environ.get("TEST_ADMIN_ID", "")
    if not test_user_id or not test_admin_id:
        pytest.skip("No test users available")
    circle = await anc_any.teams.create("test_nc_py_api_team_mm")
    try:
        added = await anc_any.teams.add_members(
            circle.circle_id,
            [
                {"id": test_user_id, "type": int(MemberType.USER)},
                {"id": test_admin_id, "type": int(MemberType.USER)},
            ],
        )
        assert isinstance(added, list)
        assert len(added) >= 2
        for m in added:
            assert isinstance(m, Member)

        members = await anc_any.teams.get_members(circle.circle_id)
        user_ids = [m.user_id for m in members]
        assert test_user_id in user_ids
        assert test_admin_id in user_ids
    finally:
        with contextlib.suppress(NextcloudException):
            await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_member_level(anc_any):
    test_user_id = environ.get("TEST_USER_ID", "")
    if not test_user_id:
        pytest.skip("No test user available")
    circle = await anc_any.teams.create("test_nc_py_api_team_ml")
    try:
        await anc_any.teams.add_member(circle.circle_id, test_user_id, MemberType.USER)
        members = await anc_any.teams.get_members(circle.circle_id)
        user_member = next(m for m in members if m.user_id == test_user_id)

        result = await anc_any.teams.set_member_level(
            circle.circle_id, user_member.member_id, MemberLevel.MODERATOR
        )
        assert isinstance(result, Member)
        assert result.level == MemberLevel.MODERATOR

        members = await anc_any.teams.get_members(circle.circle_id)
        user_member = next(m for m in members if m.user_id == test_user_id)
        assert user_member.level == MemberLevel.MODERATOR

        result = await anc_any.teams.set_member_level(
            circle.circle_id, user_member.member_id, MemberLevel.MEMBER
        )
        assert result.level == MemberLevel.MEMBER
    finally:
        with contextlib.suppress(NextcloudException):
            await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_join_leave(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_jl")
    try:
        new_config = CircleConfig.VISIBLE | CircleConfig.OPEN
        await anc_any.teams.edit_config(circle.circle_id, int(new_config))

        test_user_id = environ.get("TEST_USER_ID", "")
        test_user_pass = environ.get("TEST_USER_PASS", "")
        if not test_user_id or not test_user_pass:
            pytest.skip("No test user available")

        from nc_py_api import AsyncNextcloud

        anc_user = AsyncNextcloud(
            nextcloud_url=environ.get("NEXTCLOUD_URL", "http://nextcloud.ncpyapi:13080"),
            nc_auth_user=test_user_id,
            nc_auth_pass=test_user_pass,
        )
        joined = await anc_user.teams.join(circle.circle_id)
        assert isinstance(joined, Circle)

        members = await anc_any.teams.get_members(circle.circle_id)
        user_ids = [m.user_id for m in members]
        assert test_user_id in user_ids

        left = await anc_user.teams.leave(circle.circle_id)
        assert isinstance(left, Circle)

        members = await anc_any.teams.get_members(circle.circle_id)
        user_ids = [m.user_id for m in members]
        assert test_user_id not in user_ids
    finally:
        with contextlib.suppress(NextcloudException):
            await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_destroy_nonexistent(anc_any):
    with pytest.raises(NextcloudException):
        await anc_any.teams.destroy("nonexistent_circle_id_12345")


@pytest.mark.asyncio(scope="session")
async def test_teams_personal_circle(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_pc", personal=True)
    try:
        assert isinstance(circle, Circle)
        assert circle.config & CircleConfig.PERSONAL
    finally:
        await anc_any.teams.destroy(circle.circle_id)


@pytest.mark.asyncio(scope="session")
async def test_teams_local_circle(anc_any):
    circle = await anc_any.teams.create("test_nc_py_api_team_lc", local=True)
    try:
        assert isinstance(circle, Circle)
        assert circle.config & CircleConfig.LOCAL
    finally:
        await anc_any.teams.destroy(circle.circle_id)
