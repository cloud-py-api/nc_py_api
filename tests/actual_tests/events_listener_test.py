import pytest

from nc_py_api import NextcloudExceptionNotFound


def test_events_registration(nc_app):
    nc_app.events_listener.register(
        "node_event",
        "/some_url",
    )
    result = nc_app.events_listener.get_entry("node_event")
    assert result.event_type == "node_event"
    assert result.action_handler == "some_url"
    assert result.event_subtypes == []
    nc_app.events_listener.register(
        "node_event", callback_url="/new_url", event_subtypes=["NodeCreatedEvent", "NodeRenamedEvent"]
    )
    result = nc_app.events_listener.get_entry("node_event")
    assert result.event_type == "node_event"
    assert result.action_handler == "new_url"
    assert result.event_subtypes == ["NodeCreatedEvent", "NodeRenamedEvent"]
    nc_app.events_listener.unregister(result.event_type)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.events_listener.unregister(result.event_type, not_fail=False)
    nc_app.events_listener.unregister(result.event_type)
    assert str(result).find("event_type=") != -1


@pytest.mark.asyncio(scope="session")
async def test_events_registration_async(anc_app):
    await anc_app.events_listener.register(
        "node_event",
        "/some_url",
    )
    result = await anc_app.events_listener.get_entry("node_event")
    assert result.event_type == "node_event"
    assert result.action_handler == "some_url"
    assert result.event_subtypes == []
    await anc_app.events_listener.register(
        "node_event", callback_url="/new_url", event_subtypes=["NodeCreatedEvent", "NodeRenamedEvent"]
    )
    result = await anc_app.events_listener.get_entry("node_event")
    assert result.event_type == "node_event"
    assert result.action_handler == "new_url"
    assert result.event_subtypes == ["NodeCreatedEvent", "NodeRenamedEvent"]
    await anc_app.events_listener.unregister(result.event_type)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_app.events_listener.unregister(result.event_type, not_fail=False)
    await anc_app.events_listener.unregister(result.event_type)
    assert str(result).find("event_type=") != -1
