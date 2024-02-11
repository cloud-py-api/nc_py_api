import copy

import pytest

from nc_py_api import NextcloudExceptionNotFound, ex_app

SETTINGS_EXAMPLE = ex_app.SettingsForm(
    id="test_id",
    section_type="admin",
    section_id="test_section_id",
    title="Some title",
    description="Some description",
    fields=[
        ex_app.SettingsField(
            id="field1",
            title="Multi-selection",
            description="Select some option setting",
            type=ex_app.SettingsFieldType.MULTI_SELECT,
            default=["foo", "bar"],
            placeholder="Select some multiple options",
            options=["foo", "bar", "baz"],
        ),
    ],
)


@pytest.mark.require_nc(major=29)
def test_register_ui_settings(nc_app):
    nc_app.ui.settings.register_form(SETTINGS_EXAMPLE)
    result = nc_app.ui.settings.get_entry(SETTINGS_EXAMPLE.id)
    assert result == SETTINGS_EXAMPLE
    nc_app.ui.settings.unregister_form(SETTINGS_EXAMPLE.id)
    assert nc_app.ui.settings.get_entry(SETTINGS_EXAMPLE.id) is None
    nc_app.ui.settings.unregister_form(SETTINGS_EXAMPLE.id)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.settings.unregister_form(SETTINGS_EXAMPLE.id, not_fail=False)
    nc_app.ui.settings.register_form(SETTINGS_EXAMPLE)
    result = nc_app.ui.settings.get_entry(SETTINGS_EXAMPLE.id)
    assert result.description == SETTINGS_EXAMPLE.description
    new_settings = copy.copy(SETTINGS_EXAMPLE)
    new_settings.description = "new desc"
    nc_app.ui.settings.register_form(new_settings)
    result = nc_app.ui.settings.get_entry(new_settings.id)
    assert result.description == "new desc"
    nc_app.ui.settings.unregister_form(new_settings.id)
    assert nc_app.ui.settings.get_entry(new_settings.id) is None


@pytest.mark.require_nc(major=29)
@pytest.mark.asyncio(scope="session")
async def test_register_ui_settings_async(anc_app):
    await anc_app.ui.settings.register_form(SETTINGS_EXAMPLE)
    result = await anc_app.ui.settings.get_entry(SETTINGS_EXAMPLE.id)
    assert result == SETTINGS_EXAMPLE
    await anc_app.ui.settings.unregister_form(SETTINGS_EXAMPLE.id)
    assert await anc_app.ui.settings.get_entry(SETTINGS_EXAMPLE.id) is None
    await anc_app.ui.settings.unregister_form(SETTINGS_EXAMPLE.id)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_app.ui.settings.unregister_form(SETTINGS_EXAMPLE.id, not_fail=False)
    await anc_app.ui.settings.register_form(SETTINGS_EXAMPLE)
    result = await anc_app.ui.settings.get_entry(SETTINGS_EXAMPLE.id)
    assert result.description == SETTINGS_EXAMPLE.description
    new_settings = copy.copy(SETTINGS_EXAMPLE)
    new_settings.description = "new desc"
    await anc_app.ui.settings.register_form(new_settings)
    result = await anc_app.ui.settings.get_entry(new_settings.id)
    assert result.description == "new desc"
    await anc_app.ui.settings.unregister_form(new_settings.id)
    assert await anc_app.ui.settings.get_entry(new_settings.id) is None
