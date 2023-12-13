from time import time

import pytest

from nc_py_api.user_status import (
    ClearAt,
    CurrentUserStatus,
    PredefinedStatus,
    UserStatus,
)


def test_available(nc):
    assert nc.user_status.available


@pytest.mark.asyncio(scope="session")
async def test_available_async(anc):
    assert await anc.user_status.available


def compare_user_statuses(p1: UserStatus, p2: UserStatus):
    assert p1.user_id == p2.user_id
    assert p1.status_message == p2.status_message
    assert p1.status_icon == p2.status_icon
    assert p1.status_clear_at == p2.status_clear_at
    assert p1.status_type == p2.status_type


def _test_get_status(r1: CurrentUserStatus, message):
    assert r1.user_id == "admin"
    assert r1.status_icon is None
    assert r1.status_clear_at is None
    if message == "":
        message = None
    assert r1.status_message == message
    assert r1.status_id is None
    assert not r1.message_predefined
    assert str(r1).find("status_id=") != -1


@pytest.mark.parametrize("message", ("1 2 3", None, ""))
def test_get_status(nc, message):
    nc.user_status.set_status(message)
    r1 = nc.user_status.get_current()
    r2 = nc.user_status.get(nc.user)
    compare_user_statuses(r1, r2)
    _test_get_status(r1, message)


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("message", ("1 2 3", None, ""))
async def test_get_status_async(anc, message):
    await anc.user_status.set_status(message)
    r1 = await anc.user_status.get_current()
    r2 = await anc.user_status.get(await anc.user)
    compare_user_statuses(r1, r2)
    _test_get_status(r1, message)


def test_get_status_non_existent_user(nc):
    assert nc.user_status.get("no such user") is None


@pytest.mark.asyncio(scope="session")
async def test_get_status_non_existent_user_async(anc):
    assert await anc.user_status.get("no such user") is None


def _test_get_predefined(r: list[PredefinedStatus]):
    assert isinstance(r, list)
    assert r
    for i in r:
        assert isinstance(i.status_id, str)
        assert isinstance(i.message, str)
        assert isinstance(i.icon, str)
        assert isinstance(i.clear_at, ClearAt) or i.clear_at is None


def test_get_predefined(nc):
    r = nc.user_status.get_predefined()
    if nc.srv_version["major"] < 27:
        assert r == []
    else:
        _test_get_predefined(r)


@pytest.mark.asyncio(scope="session")
async def test_get_predefined_async(anc):
    r = await anc.user_status.get_predefined()
    if (await anc.srv_version)["major"] < 27:
        assert r == []
    else:
        _test_get_predefined(r)


def test_get_list(nc):
    r_all = nc.user_status.get_list()
    assert r_all
    assert isinstance(r_all, list)
    r_current = nc.user_status.get_current()
    for i in r_all:
        if i.user_id == nc.user:
            compare_user_statuses(i, r_current)
        assert str(i).find("status_type=") != -1


@pytest.mark.asyncio(scope="session")
async def test_get_list_async(anc):
    r_all = await anc.user_status.get_list()
    assert r_all
    assert isinstance(r_all, list)
    r_current = await anc.user_status.get_current()
    for i in r_all:
        if i.user_id == anc.user:
            compare_user_statuses(i, r_current)
        assert str(i).find("status_type=") != -1


def test_set_status(nc):
    time_clear = int(time()) + 60
    nc.user_status.set_status("cool status", time_clear)
    r = nc.user_status.get_current()
    assert r.status_message == "cool status"
    assert r.status_clear_at == time_clear
    assert r.status_icon is None
    nc.user_status.set_status("Sick!", status_icon="🤒")
    r = nc.user_status.get_current()
    assert r.status_message == "Sick!"
    assert r.status_clear_at is None
    assert r.status_icon == "🤒"
    nc.user_status.set_status(None)
    r = nc.user_status.get_current()
    assert r.status_message is None
    assert r.status_clear_at is None
    assert r.status_icon is None


@pytest.mark.asyncio(scope="session")
async def test_set_status_async(anc):
    time_clear = int(time()) + 60
    await anc.user_status.set_status("cool status", time_clear)
    r = await anc.user_status.get_current()
    assert r.status_message == "cool status"
    assert r.status_clear_at == time_clear
    assert r.status_icon is None
    await anc.user_status.set_status("Sick!", status_icon="🤒")
    r = await anc.user_status.get_current()
    assert r.status_message == "Sick!"
    assert r.status_clear_at is None
    assert r.status_icon == "🤒"
    await anc.user_status.set_status(None)
    r = await anc.user_status.get_current()
    assert r.status_message is None
    assert r.status_clear_at is None
    assert r.status_icon is None


@pytest.mark.parametrize("value", ("online", "away", "dnd", "invisible", "offline"))
def test_set_status_type(nc, value):
    nc.user_status.set_status_type(value)
    r = nc.user_status.get_current()
    assert r.status_type == value
    assert r.status_type_defined


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("value", ("online", "away", "dnd", "invisible", "offline"))
async def test_set_status_type_async(anc, value):
    await anc.user_status.set_status_type(value)
    r = await anc.user_status.get_current()
    assert r.status_type == value
    assert r.status_type_defined


@pytest.mark.parametrize("clear_at", (None, int(time()) + 360))
def test_set_predefined(nc, clear_at):
    if nc.srv_version["major"] < 27:
        nc.user_status.set_predefined("meeting")
    else:
        predefined_statuses = nc.user_status.get_predefined()
        for i in predefined_statuses:
            nc.user_status.set_predefined(i.status_id, clear_at)
            r = nc.user_status.get_current()
            assert r.status_message == i.message
            assert r.status_id == i.status_id
            assert r.message_predefined
            assert r.status_clear_at == clear_at


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize("clear_at", (None, int(time()) + 360))
async def test_set_predefined_async(anc, clear_at):
    if (await anc.srv_version)["major"] < 27:
        await anc.user_status.set_predefined("meeting")
    else:
        predefined_statuses = await anc.user_status.get_predefined()
        for i in predefined_statuses:
            await anc.user_status.set_predefined(i.status_id, clear_at)
            r = await anc.user_status.get_current()
            assert r.status_message == i.message
            assert r.status_id == i.status_id
            assert r.message_predefined
            assert r.status_clear_at == clear_at


@pytest.mark.require_nc(major=27)
def test_get_back_status_from_from_empty_user(nc_app):
    orig_user = nc_app._session.user
    nc_app._session.set_user("")
    try:
        with pytest.raises(ValueError):
            nc_app.user_status.get_backup_status("")
    finally:
        nc_app._session.set_user(orig_user)


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=27)
async def test_get_back_status_from_from_empty_user_async(anc_app):
    orig_user = await anc_app._session.user
    anc_app._session.set_user("")
    try:
        with pytest.raises(ValueError):
            await anc_app.user_status.get_backup_status("")
    finally:
        anc_app._session.set_user(orig_user)


@pytest.mark.require_nc(major=27)
def test_get_back_status_from_from_non_exist_user(nc):
    assert nc.user_status.get_backup_status("mёm_m-m.l") is None


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=27)
async def test_get_back_status_from_from_non_exist_user_async(anc):
    assert await anc.user_status.get_backup_status("mёm_m-m.l") is None


@pytest.mark.require_nc(major=27)
def test_restore_from_non_existing_back_status(nc):
    assert nc.user_status.restore_backup_status("no such backup status") is None


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=27)
async def test_restore_from_non_existing_back_status_async(anc):
    assert await anc.user_status.restore_backup_status("no such backup status") is None
