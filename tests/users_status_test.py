from time import time

import pytest
from gfixture import NC_TO_TEST, NC_VERSION

from nc_py_api.users.status import ClearAt, UserStatus


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_available(nc):
    assert nc.users.status.available


def compare_user_statuses(p1: UserStatus, p2: UserStatus):
    assert p1.user_id == p2.user_id
    assert p1.message == p2.message
    assert p1.icon == p2.icon
    assert p1.clear_at == p2.clear_at
    assert p1.status_type == p2.status_type


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("message", ("1 2 3", None, ""))
def test_get_status(nc, message):
    nc.users.status.set_status(message)
    r1 = nc.users.status.get_current()
    r2 = nc.users.status.get(nc.user)
    compare_user_statuses(r1, r2)
    assert r1.user_id == "admin"
    assert r1.icon is None
    assert r1.clear_at is None
    if message == "":
        message = None
    assert r1.message == message
    assert r1.status_id is None
    assert not r1.predefined


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_status_non_existent_user(nc):
    assert nc.users.status.get("no such user") is None


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_predefined(nc):
    r = nc.users.status.get_predefined()
    if nc.srv_version["major"] < 27:
        assert r == []
    else:
        assert isinstance(r, list)
        assert r
        for i in r:
            assert isinstance(i.status_id, str)
            assert isinstance(i.message, str)
            assert isinstance(i.icon, str)
            assert isinstance(i.clear_at, ClearAt) or i.clear_at is None


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_list(nc):
    r_all = nc.users.status.get_list()
    assert r_all
    assert isinstance(r_all, list)
    r_current = nc.users.status.get_current()
    for i in r_all:
        if i.user_id == nc.user:
            compare_user_statuses(i, r_current)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_set_status(nc):
    time_clear = int(time()) + 60
    nc.users.status.set_status("cool status", time_clear)
    r = nc.users.status.get_current()
    assert r.message == "cool status"
    assert r.clear_at == time_clear
    assert r.icon is None
    nc.users.status.set_status("Sick!", status_icon="🤒")
    r = nc.users.status.get_current()
    assert r.message == "Sick!"
    assert r.clear_at is None
    assert r.icon == "🤒"
    nc.users.status.set_status(None)
    r = nc.users.status.get_current()
    assert r.message is None
    assert r.clear_at is None
    assert r.icon is None


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("value", ("online", "away", "dnd", "invisible", "offline"))
def test_set_status_type(nc, value):
    nc.users.status.set_status_type(value)
    r = nc.users.status.get_current()
    assert r.status_type == value
    assert r.status_type_defined


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("clear_at", (None, int(time()) + 360))
def test_set_predefined(nc, clear_at):
    if nc.srv_version["major"] < 27:
        nc.users.status.set_predefined("meeting")
    else:
        predefined_statuses = nc.users.status.get_predefined()
        for i in predefined_statuses:
            nc.users.status.set_predefined(i.status_id, clear_at)
            r = nc.users.status.get_current()
            assert r.message == i.message
            assert r.status_id == i.status_id
            assert r.predefined
            assert r.clear_at == clear_at


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.skipif(NC_VERSION["major"] < 27, reason="Run only on NC27+")
def test_get_back_status_from_from_empty_user(nc):
    orig_user = nc._session.user
    nc._session.user = ""
    try:
        with pytest.raises(ValueError):
            nc.users.status.get_backup_status("")
    finally:
        nc._session.user = orig_user


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.skipif(NC_VERSION["major"] < 27, reason="Run only on NC27+")
def test_get_back_status_from_from_non_exist_user(nc):
    assert nc.users.status.get_backup_status("mёm_m-m.l") is None


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.skipif(NC_VERSION["major"] < 27, reason="Run only on NC27+")
def test_restore_from_non_existing_back_status(nc):
    assert nc.users.status.restore_backup_status("no such backup status") is None
