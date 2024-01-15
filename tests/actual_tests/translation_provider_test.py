import pytest

from nc_py_api import NextcloudExceptionNotFound

FROM_LANG1 = {"ar_AR": "Arabic", "de_DE": "German", "uk_UA": "Ukrainian"}
TO_LANG1 = {"zh_CN": "Chinese", "en_US": "English", "es_ES": "Spanish"}


@pytest.mark.require_nc(major=29)
def test_translation_provider(nc_app):
    nc_app.providers.translations.register(
        "test_id",
        "Test #1 Prov",
        "/some_url",
        FROM_LANG1,
        TO_LANG1,
    )
    result = nc_app.providers.translations.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Test #1 Prov"
    assert result.action_handler == "some_url"
    assert result.from_languages == FROM_LANG1
    assert result.to_languages == TO_LANG1
    nc_app.providers.translations.register(
        "test_id2",
        "Test #2 Prov",
        "some_url2",
        {"pl_PL": "Polish"},
        {"tr_TR": "Turkish"},
    )
    result2 = nc_app.providers.translations.get_entry("test_id2")
    assert result2.name == "test_id2"
    assert result2.display_name == "Test #2 Prov"
    assert result2.action_handler == "some_url2"
    assert result2.from_languages == {"pl_PL": "Polish"}
    assert result2.to_languages == {"tr_TR": "Turkish"}
    nc_app.providers.translations.register(
        "test_id",
        "Renamed",
        "/new_url",
        {"kk_KZ": "Kazakh"},
        {"it_IT": "Italian"},
    )
    result = nc_app.providers.translations.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Renamed"
    assert result.action_handler == "new_url"
    assert result.from_languages == {"kk_KZ": "Kazakh"}
    assert result.to_languages == {"it_IT": "Italian"}
    nc_app.providers.translations.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.providers.translations.unregister(result.name, not_fail=False)
    nc_app.providers.translations.unregister(result.name)
    nc_app.providers.translations.unregister(result2.name, not_fail=False)
    assert nc_app.providers.translations.get_entry(result2.name) is None
    assert str(result).find("name=") != -1


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=29)
async def test_translation_async(anc_app):
    await anc_app.providers.translations.register(
        "test_id",
        "Test #1 Prov",
        "/some_url",
        FROM_LANG1,
        TO_LANG1,
    )
    result = await anc_app.providers.translations.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Test #1 Prov"
    assert result.action_handler == "some_url"
    assert result.from_languages == FROM_LANG1
    assert result.to_languages == TO_LANG1
    await anc_app.providers.translations.register(
        "test_id2",
        "Test #2 Prov",
        "some_url2",
        {"pl_PL": "Polish"},
        {"tr_TR": "Turkish"},
    )
    result2 = await anc_app.providers.translations.get_entry("test_id2")
    assert result2.name == "test_id2"
    assert result2.display_name == "Test #2 Prov"
    assert result2.action_handler == "some_url2"
    assert result.from_languages == {"pl_PL": "Polish"}
    assert result.to_languages == {"tr_TR": "Turkish"}
    await anc_app.providers.translations.register(
        "test_id",
        "Renamed",
        "/new_url",
        {"kk_KZ": "Kazakh"},
        {"it_IT": "Italian"},
    )
    result = await anc_app.providers.translations.get_entry("test_id")
    assert result.name == "test_id"
    assert result.display_name == "Renamed"
    assert result.action_handler == "new_url"
    assert result.from_languages == {"kk_KZ": "Kazakh"}
    assert result.to_languages == {"it_IT": "Italian"}
    await anc_app.providers.translations.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_app.providers.translations.unregister(result.name, not_fail=False)
    await anc_app.providers.translations.unregister(result.name)
    await anc_app.providers.translations.unregister(result2.name, not_fail=False)
    assert await anc_app.providers.translations.get_entry(result2.name) is None
    assert str(result).find("name=") != -1


@pytest.mark.require_nc(major=29)
def test_translations_provider_fail_report(nc_app):
    nc_app.providers.translations.report_result(999999)


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=29)
async def test_translations_provider_fail_report_async(anc_app):
    await anc_app.providers.translations.report_result(999999)
