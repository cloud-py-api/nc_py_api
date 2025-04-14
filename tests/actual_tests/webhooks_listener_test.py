import pytest


def test_events_registration(nc_app):
    assert isinstance(nc_app.webhooks.get_list(), list)
    assert isinstance(nc_app.webhooks.unregister_all(), int)
    assert nc_app.webhooks.unregister_all() == 0
    assert nc_app.webhooks.get_list() == []
    webhook_info = nc_app.webhooks.register(
        "POST",
        "/some_url",
        "OCP\\Files\\Events\\Node\\NodeCreatedEvent",
    )
    result = nc_app.webhooks.get_entry(webhook_info.webhook_id)
    assert result.webhook_id == webhook_info.webhook_id
    assert result.app_id == "nc_py_api"
    assert result.http_method == "POST"
    assert result.uri == "/some_url"
    assert result.auth_method == "none"
    assert result.auth_data == {}
    assert result.user_id_filter == ""
    assert result.event_filter == []
    assert result.event == "OCP\\Files\\Events\\Node\\NodeCreatedEvent"
    result = nc_app.webhooks.update(
        webhook_info.webhook_id, http_method="PUT", uri="/some_url2", event="OCP\\Files\\Events\\Node\\NodeCreatedEvent"
    )
    assert result.webhook_id == webhook_info.webhook_id
    nc_app.webhooks.unregister(webhook_info.webhook_id)
    nc_app.webhooks.unregister(webhook_info.webhook_id)  # removing non-existing webhook should not fail
    assert nc_app.webhooks.get_entry(webhook_info.webhook_id) is None


@pytest.mark.asyncio(scope="session")
async def test_events_registration_async(anc_app):
    assert isinstance(await anc_app.webhooks.get_list(), list)
    assert isinstance(await anc_app.webhooks.unregister_all(), int)
    assert await anc_app.webhooks.unregister_all() == 0
    assert await anc_app.webhooks.get_list() == []
    webhook_info = await anc_app.webhooks.register(
        "POST",
        "/some_url",
        "OCP\\Files\\Events\\Node\\NodeCreatedEvent",
    )
    result = await anc_app.webhooks.get_entry(webhook_info.webhook_id)
    assert result.webhook_id == webhook_info.webhook_id
    assert result.app_id == "nc_py_api"
    assert result.http_method == "POST"
    assert result.uri == "/some_url"
    assert result.auth_method == "none"
    assert result.auth_data == {}
    assert result.user_id_filter == ""
    assert result.event_filter == []
    assert result.event == "OCP\\Files\\Events\\Node\\NodeCreatedEvent"
    result = await anc_app.webhooks.update(
        webhook_info.webhook_id, http_method="PUT", uri="/some_url2", event="OCP\\Files\\Events\\Node\\NodeCreatedEvent"
    )
    assert result.webhook_id == webhook_info.webhook_id
    await anc_app.webhooks.unregister(webhook_info.webhook_id)
    await anc_app.webhooks.unregister(webhook_info.webhook_id)  # removing non-existing webhook should not fail
    assert await anc_app.webhooks.get_entry(webhook_info.webhook_id) is None
