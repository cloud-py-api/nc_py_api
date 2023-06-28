import pytest

from time import time


from gfixture import NC_TO_TEST, NC_VERSION


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_avalaible(nc):
    assert nc.users_statuses.avalaible


def compare_user_statuses(p1, p2):
    assert p1["userId"] == p2["userId"]
    assert p1["message"] == p2["message"]
    assert p1["icon"] == p2["icon"]
    assert p1["clearAt"] == p2["clearAt"]
    assert p1["status"] == p2["status"]


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("message", ("1 2 3", None, ""))
def test_get_status(nc, message):
    nc.users_statuses.set(message)
    r1 = nc.users_statuses.get_current()
    r2 = nc.users_statuses.get(nc.user)
    compare_user_statuses(r1, r2)
    assert r1["userId"] == "admin"
    assert r1["icon"] is None
    assert r1["clearAt"] is None
    if message == "":
        message = None
    assert r1["message"] == message
    assert r1["messageId"] is None
    assert not r1["messageIsPredefined"]


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.skipif(NC_VERSION.get("major", 0) < 27, reason="NC27 required.")
def test_get_predefined(nc):
    r = nc.users_statuses.get_predefined()
    assert isinstance(r, list)
    assert r
    for i in r:
        assert isinstance(i["id"], str)
        assert isinstance(i["message"], str)
        assert isinstance(i["icon"], str)
        assert isinstance(i["clearAt"], dict) or i["clearAt"] is None


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_all(nc):
    r_all = nc.users_statuses.get_all()
    assert r_all
    assert isinstance(r_all, list)
    r_current = nc.users_statuses.get_current()
    for i in r_all:
        if i["userId"] == nc.user:
            compare_user_statuses(i, r_current)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_set_status(nc):
    time_clear = int(time()) + 60
    nc.users_statuses.set("cool status", time_clear)
    r = nc.users_statuses.get_current()
    assert r["message"] == "cool status"
    assert r["clearAt"] == time_clear
    assert r["icon"] is None
    nc.users_statuses.set("Sick!", status_icon='🤒')
    r = nc.users_statuses.get_current()
    assert r["message"] == "Sick!"
    assert r["clearAt"] is None
    assert r["icon"] == '🤒'
    nc.users_statuses.set(None)
    r = nc.users_statuses.get_current()
    assert r["message"] is None
    assert r["clearAt"] is None
    assert r["icon"] is None


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("value", ("online", "away", "dnd", "invisible", "offline"))
def test_set_status_type(nc, value):
    nc.users_statuses.set_status_type(value)
    r = nc.users_statuses.get_current()
    assert r["status"] == value
    assert r["statusIsUserDefined"]


@pytest.mark.parametrize("nc", NC_TO_TEST)
@pytest.mark.parametrize("clear_at", (None, int(time()) + 360))
@pytest.mark.skipif(NC_VERSION.get("major", 0) < 27, reason="NC27 required.")
def test_set_predefined(nc, clear_at):
    predefined_statuses = nc.users_statuses.get_predefined()
    for i in predefined_statuses:
        nc.users_statuses.set_predefined(i["id"], clear_at)
        r = nc.users_statuses.get_current()
        assert r["message"] == i["message"]
        assert r["messageId"] == i["id"]
        assert r["messageIsPredefined"]
        assert r["clearAt"] == clear_at
