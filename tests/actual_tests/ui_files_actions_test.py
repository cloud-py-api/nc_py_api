import pytest

from nc_py_api import FilePermissions, FsNode, NextcloudExceptionNotFound, ex_app


def test_register_ui_file_actions(nc_app):
    nc_app.ui.files_dropdown_menu.register_ex("test_ui_action_im", "UI TEST Image", "/ui_action_test", mime="image")
    result = nc_app.ui.files_dropdown_menu.get_entry("test_ui_action_im")
    assert result.name == "test_ui_action_im"
    assert result.display_name == "UI TEST Image"
    assert result.action_handler == "ui_action_test"
    assert result.mime == "image"
    assert result.permissions == 31
    assert result.order == 0
    assert result.icon == ""
    assert result.appid == "nc_py_api"
    assert result.version == "2.0"
    nc_app.ui.files_dropdown_menu.unregister(result.name)
    nc_app.ui.files_dropdown_menu.register("test_ui_action_any", "UI TEST", "ui_action", permissions=1, order=1)
    result = nc_app.ui.files_dropdown_menu.get_entry("test_ui_action_any")
    assert result.name == "test_ui_action_any"
    assert result.display_name == "UI TEST"
    assert result.action_handler == "ui_action"
    assert result.mime == "file"
    assert result.permissions == 1
    assert result.order == 1
    assert result.icon == ""
    assert result.version == "1.0"
    nc_app.ui.files_dropdown_menu.register_ex("test_ui_action_any", "UI", "/ui_action2", icon="/img/icon.svg")
    result = nc_app.ui.files_dropdown_menu.get_entry("test_ui_action_any")
    assert result.name == "test_ui_action_any"
    assert result.display_name == "UI"
    assert result.action_handler == "ui_action2"
    assert result.mime == "file"
    assert result.permissions == 31
    assert result.order == 0
    assert result.icon == "img/icon.svg"
    assert result.version == "2.0"
    nc_app.ui.files_dropdown_menu.unregister(result.name)
    assert str(result).find("name=test_ui_action")


@pytest.mark.asyncio(scope="session")
async def test_register_ui_file_actions_async(anc_app):
    await anc_app.ui.files_dropdown_menu.register_ex(
        "test_ui_action_im", "UI TEST Image", "/ui_action_test", mime="image"
    )
    result = await anc_app.ui.files_dropdown_menu.get_entry("test_ui_action_im")
    assert result.name == "test_ui_action_im"
    assert result.display_name == "UI TEST Image"
    assert result.action_handler == "ui_action_test"
    assert result.mime == "image"
    assert result.permissions == 31
    assert result.order == 0
    assert result.icon == ""
    assert result.appid == "nc_py_api"
    assert result.version == "2.0"
    await anc_app.ui.files_dropdown_menu.unregister(result.name)
    await anc_app.ui.files_dropdown_menu.register("test_ui_action_any", "UI TEST", "ui_action", permissions=1, order=1)
    result = await anc_app.ui.files_dropdown_menu.get_entry("test_ui_action_any")
    assert result.name == "test_ui_action_any"
    assert result.display_name == "UI TEST"
    assert result.action_handler == "ui_action"
    assert result.mime == "file"
    assert result.permissions == 1
    assert result.order == 1
    assert result.icon == ""
    assert result.version == "1.0"
    await anc_app.ui.files_dropdown_menu.register_ex("test_ui_action_any", "UI", "/ui_action2", icon="/img/icon.svg")
    result = await anc_app.ui.files_dropdown_menu.get_entry("test_ui_action_any")
    assert result.name == "test_ui_action_any"
    assert result.display_name == "UI"
    assert result.action_handler == "ui_action2"
    assert result.mime == "file"
    assert result.permissions == 31
    assert result.order == 0
    assert result.icon == "img/icon.svg"
    assert result.version == "2.0"
    await anc_app.ui.files_dropdown_menu.unregister(result.name)
    assert str(result).find("name=test_ui_action")


def test_unregister_ui_file_actions(nc_app):
    nc_app.ui.files_dropdown_menu.register_ex("test_ui_action", "NcPyApi UI TEST", "/any_rel_url")
    nc_app.ui.files_dropdown_menu.unregister("test_ui_action")
    assert nc_app.ui.files_dropdown_menu.get_entry("test_ui_action") is None
    nc_app.ui.files_dropdown_menu.unregister("test_ui_action")
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.files_dropdown_menu.unregister("test_ui_action", not_fail=False)


@pytest.mark.asyncio(scope="session")
async def test_unregister_ui_file_actions_async(anc_app):
    await anc_app.ui.files_dropdown_menu.register_ex("test_ui_action", "NcPyApi UI TEST", "/any_rel_url")
    await anc_app.ui.files_dropdown_menu.unregister("test_ui_action")
    assert await anc_app.ui.files_dropdown_menu.get_entry("test_ui_action") is None
    await anc_app.ui.files_dropdown_menu.unregister("test_ui_action")
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_app.ui.files_dropdown_menu.unregister("test_ui_action", not_fail=False)


def test_ui_file_to_fs_node(nc_app):
    def ui_action_check(directory: str, fs_object: FsNode):
        permissions = 0
        if fs_object.is_readable:
            permissions += FilePermissions.PERMISSION_READ
        if fs_object.is_updatable:
            permissions += FilePermissions.PERMISSION_UPDATE
        if fs_object.is_creatable:
            permissions += FilePermissions.PERMISSION_CREATE
        if fs_object.is_deletable:
            permissions += FilePermissions.PERMISSION_DELETE
        if fs_object.is_shareable:
            permissions += FilePermissions.PERMISSION_SHARE
        fileid_str = str(fs_object.info.fileid)
        i = fs_object.file_id.find(fileid_str)
        file_info = ex_app.UiActionFileInfo(
            fileId=fs_object.info.fileid,
            name=fs_object.name,
            directory=directory,
            etag=fs_object.etag,
            mime=fs_object.info.mimetype,
            fileType="dir" if fs_object.is_dir else "file",
            mtime=int(fs_object.info.last_modified.timestamp()),
            size=fs_object.info.size,
            favorite=str(fs_object.info.favorite),
            permissions=permissions,
            userId=fs_object.user,
            shareOwner="some_user" if fs_object.is_shared else None,
            shareOwnerId="some_user_id" if fs_object.is_shared else None,
            instanceId=fs_object.file_id[i + len(fileid_str) :],
        )
        fs_node = file_info.to_fs_node()
        assert isinstance(fs_node, FsNode)
        assert fs_node.etag == fs_object.etag
        assert fs_node.name == fs_object.name
        assert fs_node.user_path == fs_object.user_path
        assert fs_node.full_path == fs_object.full_path
        assert fs_node.file_id == fs_object.file_id
        assert fs_node.is_dir == fs_object.is_dir
        assert fs_node.info.mimetype == fs_object.info.mimetype
        assert fs_node.info.permissions == fs_object.info.permissions
        assert fs_node.info.last_modified == fs_object.info.last_modified
        assert fs_node.info.favorite == fs_object.info.favorite
        assert fs_node.info.content_length == fs_object.info.content_length
        assert fs_node.info.size == fs_object.info.size
        assert fs_node.info.fileid == fs_object.info.fileid

    for each_file in nc_app.files.listdir():
        ui_action_check(directory="/", fs_object=each_file)
    for each_file in nc_app.files.listdir("test_dir"):
        ui_action_check(directory="/test_dir", fs_object=each_file)
