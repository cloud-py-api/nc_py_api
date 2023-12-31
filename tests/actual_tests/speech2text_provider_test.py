import pytest

from nc_py_api import NextcloudExceptionNotFound


@pytest.mark.require_nc(major=29)
def test_speech2text_provider(nc_app):
    nc_app.providers.speech_to_text.register("test_id", "Test #1 Prov", "/some_url")
    result = nc_app.providers.speech_to_text.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Test #1 Prov"
    assert result.action_handler == "some_url"
    nc_app.providers.speech_to_text.register("test_id2", "Test #2 Prov", "some_url2")
    result2 = nc_app.providers.speech_to_text.get_entry("test_id2")
    assert result2.name == "test_id2"
    assert result2.display_name == "Test #2 Prov"
    assert result2.action_handler == "some_url2"
    nc_app.providers.speech_to_text.register("test_id", "Renamed", "/new_url")
    result = nc_app.providers.speech_to_text.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Renamed"
    assert result.action_handler == "new_url"
    nc_app.providers.speech_to_text.unregister(result.name)
    nc_app.providers.speech_to_text.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.providers.speech_to_text.unregister(result.name, not_fail=False)
    nc_app.providers.speech_to_text.unregister(result2.name, not_fail=False)
    assert str(result).find("name=") != -1


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=29)
async def test_speech2text_provider_async(anc_app):
    await anc_app.providers.speech_to_text.register("test_id", "Test #1 Prov", "/some_url")
    result = await anc_app.providers.speech_to_text.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Test #1 Prov"
    assert result.action_handler == "some_url"
    await anc_app.providers.speech_to_text.register("test_id2", "Test #2 Prov", "some_url2")
    result2 = await anc_app.providers.speech_to_text.get_entry("test_id2")
    assert result2.name == "test_id2"
    assert result2.display_name == "Test #2 Prov"
    assert result2.action_handler == "some_url2"
    await anc_app.providers.speech_to_text.register("test_id", "Renamed", "/new_url")
    result = await anc_app.providers.speech_to_text.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Renamed"
    assert result.action_handler == "new_url"
    await anc_app.providers.speech_to_text.unregister(result.name)
    await anc_app.providers.speech_to_text.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_app.providers.speech_to_text.unregister(result.name, not_fail=False)
    await anc_app.providers.speech_to_text.unregister(result2.name, not_fail=False)
    assert str(result).find("name=") != -1
