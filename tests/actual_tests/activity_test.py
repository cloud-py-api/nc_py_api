import datetime

import pytest

from nc_py_api.activity import Activity


def test_get_filters(nc_any):
    if nc_any.activity.available is False:
        pytest.skip("Activity App is not installed")
    r = nc_any.activity.get_filters()
    assert r
    for i in r:
        assert i.filter_id
        assert isinstance(i.icon, str)
        assert i.name
        assert isinstance(i.priority, int)
        assert str(i).find("name=") != -1


@pytest.mark.asyncio(scope="session")
async def test_get_filters_async(anc_any):
    if await anc_any.activity.available is False:
        pytest.skip("Activity App is not installed")
    r = await anc_any.activity.get_filters()
    assert r
    for i in r:
        assert i.filter_id
        assert isinstance(i.icon, str)
        assert i.name
        assert isinstance(i.priority, int)
        assert str(i).find("name=") != -1


def _get_activities(r: list[Activity]):
    assert r
    for i in r:
        assert i.activity_id
        assert isinstance(i.app, str)
        assert isinstance(i.activity_type, str)
        assert isinstance(i.actor_id, str)
        assert isinstance(i.subject, str)
        assert isinstance(i.subject_rich, list)
        assert isinstance(i.message, str)
        assert isinstance(i.message_rich, list)
        assert isinstance(i.object_type, str)
        assert isinstance(i.object_id, int)
        assert isinstance(i.object_name, str)
        assert isinstance(i.objects, dict)
        assert isinstance(i.link, str)
        assert isinstance(i.icon, str)
        assert i.time > datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        assert str(i).find("app=") != -1


def test_get_activities(nc_any):
    if nc_any.activity.available is False:
        pytest.skip("Activity App is not installed")
    with pytest.raises(ValueError):
        nc_any.activity.get_activities(object_id=4)
    r = nc_any.activity.get_activities(since=True)
    _get_activities(r)
    r2 = nc_any.activity.get_activities(since=True)
    if r2:
        old_activities_id = [i.activity_id for i in r]
        assert r2[0].activity_id not in old_activities_id
        assert r2[-1].activity_id not in old_activities_id
    assert len(nc_any.activity.get_activities(since=0, limit=1)) == 1
    while True:
        if not nc_any.activity.get_activities(since=True):
            break


@pytest.mark.asyncio(scope="session")
async def test_get_activities_async(anc_any):
    if await anc_any.activity.available is False:
        pytest.skip("Activity App is not installed")
    with pytest.raises(ValueError):
        await anc_any.activity.get_activities(object_id=4)
    r = await anc_any.activity.get_activities(since=True)
    _get_activities(r)
    r2 = await anc_any.activity.get_activities(since=True)
    if r2:
        old_activities_id = [i.activity_id for i in r]
        assert r2[0].activity_id not in old_activities_id
        assert r2[-1].activity_id not in old_activities_id
    assert len(await anc_any.activity.get_activities(since=0, limit=1)) == 1
    while True:
        if not await anc_any.activity.get_activities(since=True):
            break
