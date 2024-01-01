import pytest

from nc_py_api import NextcloudExceptionNotFound


@pytest.mark.require_nc(major=29)
def test_text_processing_provider(nc_app):
    nc_app.providers.text_processing.register("test_id", "Test #1 Prov", "/some_url", "free_prompt")
    result = nc_app.providers.text_processing.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Test #1 Prov"
    assert result.action_handler == "some_url"
    nc_app.providers.text_processing.register("test_id2", "Test #2 Prov", "some_url2", "free_prompt")
    result2 = nc_app.providers.text_processing.get_entry("test_id2")
    assert result2.name == "test_id2"
    assert result2.display_name == "Test #2 Prov"
    assert result2.action_handler == "some_url2"
    nc_app.providers.text_processing.register("test_id", "Renamed", "/new_url", "free_prompt")
    result = nc_app.providers.text_processing.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Renamed"
    assert result.action_handler == "new_url"
    assert result.task_type == "free_prompt"
    nc_app.providers.text_processing.unregister(result.name)
    nc_app.providers.text_processing.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.providers.text_processing.unregister(result.name, not_fail=False)
    nc_app.providers.text_processing.unregister(result2.name, not_fail=False)
    assert nc_app.providers.text_processing.get_entry(result2.name) is None
    assert str(result).find("type=free_prompt") != -1


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=29)
async def test_text_processing_provider_async(anc_app):
    await anc_app.providers.text_processing.register("test_id", "Test #1 Prov", "/some_url", "free_prompt")
    result = await anc_app.providers.text_processing.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Test #1 Prov"
    assert result.action_handler == "some_url"
    await anc_app.providers.text_processing.register("test_id2", "Test #2 Prov", "some_url2", "free_prompt")
    result2 = await anc_app.providers.text_processing.get_entry("test_id2")
    assert result2.name == "test_id2"
    assert result2.display_name == "Test #2 Prov"
    assert result2.action_handler == "some_url2"
    await anc_app.providers.text_processing.register("test_id", "Renamed", "/new_url", "free_prompt")
    result = await anc_app.providers.text_processing.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Renamed"
    assert result.action_handler == "new_url"
    assert result.task_type == "free_prompt"
    await anc_app.providers.text_processing.unregister(result.name)
    await anc_app.providers.text_processing.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_app.providers.text_processing.unregister(result.name, not_fail=False)
    await anc_app.providers.text_processing.unregister(result2.name, not_fail=False)
    assert await anc_app.providers.text_processing.get_entry(result2.name) is None
    assert str(result).find("type=free_prompt") != -1
