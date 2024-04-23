import pytest

from nc_py_api import NextcloudExceptionNotFound


def test_occ_commands_registration(nc_app):
    nc_app.occ_commands.register(
        "test_occ_name",
        "/some_url",
    )
    result = nc_app.occ_commands.get_entry("test_occ_name")
    assert result.name == "test_occ_name"
    assert result.description == ""
    assert result.action_handler == "some_url"
    assert result.hidden is False
    assert result.usages == []
    assert result.arguments == []
    assert result.options == []
    nc_app.occ_commands.register(
        "test_occ_name2",
        "some_url2",
        description="desc",
        arguments=[
            {
                "name": "argument_name",
                "mode": "required",
                "description": "Description of the argument",
                "default": "default_value",
            },
        ],
        options=[],
    )
    result2 = nc_app.occ_commands.get_entry("test_occ_name2")
    assert result2.name == "test_occ_name2"
    assert result2.description == "desc"
    assert result2.action_handler == "some_url2"
    assert result2.hidden is False
    assert result2.usages == []
    assert result2.arguments == [
        {
            "name": "argument_name",
            "mode": "required",
            "description": "Description of the argument",
            "default": "default_value",
        }
    ]
    assert result2.options == []
    nc_app.occ_commands.register(
        "test_occ_name",
        description="new desc",
        callback_url="/new_url",
    )
    result = nc_app.occ_commands.get_entry("test_occ_name")
    assert result.name == "test_occ_name"
    assert result.description == "new desc"
    assert result.action_handler == "new_url"
    nc_app.occ_commands.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.occ_commands.unregister(result.name, not_fail=False)
    nc_app.occ_commands.unregister(result.name)
    nc_app.occ_commands.unregister(result2.name, not_fail=False)
    assert nc_app.occ_commands.get_entry(result2.name) is None
    assert str(result).find("name=") != -1


@pytest.mark.asyncio(scope="session")
async def test_occ_commands_registration_async(anc_app):
    await anc_app.occ_commands.register(
        "test_occ_name",
        "/some_url",
    )
    result = await anc_app.occ_commands.get_entry("test_occ_name")
    assert result.name == "test_occ_name"
    assert result.description == ""
    assert result.action_handler == "some_url"
    assert result.hidden is False
    assert result.usages == []
    assert result.arguments == []
    assert result.options == []
    await anc_app.occ_commands.register(
        "test_occ_name2",
        "some_url2",
        description="desc",
        arguments=[
            {
                "name": "argument_name",
                "mode": "required",
                "description": "Description of the argument",
                "default": "default_value",
            },
        ],
        options=[],
    )
    result2 = await anc_app.occ_commands.get_entry("test_occ_name2")
    assert result2.name == "test_occ_name2"
    assert result2.description == "desc"
    assert result2.action_handler == "some_url2"
    assert result2.hidden is False
    assert result2.usages == []
    assert result2.arguments == [
        {
            "name": "argument_name",
            "mode": "required",
            "description": "Description of the argument",
            "default": "default_value",
        }
    ]
    assert result2.options == []
    await anc_app.occ_commands.register(
        "test_occ_name",
        description="new desc",
        callback_url="/new_url",
    )
    result = await anc_app.occ_commands.get_entry("test_occ_name")
    assert result.name == "test_occ_name"
    assert result.description == "new desc"
    assert result.action_handler == "new_url"
    await anc_app.occ_commands.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_app.occ_commands.unregister(result.name, not_fail=False)
    await anc_app.occ_commands.unregister(result.name)
    await anc_app.occ_commands.unregister(result2.name, not_fail=False)
    assert await anc_app.occ_commands.get_entry(result2.name) is None
    assert str(result).find("name=") != -1
