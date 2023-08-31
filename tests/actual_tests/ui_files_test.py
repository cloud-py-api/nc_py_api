from os import environ
from time import sleep

import pytest

from nc_py_api import FilePermissions, FsNode, NextcloudExceptionNotFound, ex_app

pytest.importorskip("selenium", reason="Selenium is not installed")

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as exp_cond
from selenium.webdriver.support.wait import WebDriverWait


@pytest.mark.skipif(environ.get("CI", None) is not None, reason="do not work on GitHub")
@pytest.mark.skipif(
    not environ.get("NC_AUTH_USER", None) or not environ.get("NC_AUTH_PASS", None),
    reason="needs username & password for tests.",
)
def test_register_ui_file_actions(nc_app):
    tmp_png = nc_app.files.by_path("test_dir/test_generated_image.png")
    nc_app.ui.files_dropdown_menu.register("test_ui_action_im", "UI TEST Image", "/ui_action_test", mime="image")
    nc_app.ui.files_dropdown_menu.register("test_ui_action_txt", "UI TEST Txt", "/ui_action_test", mime="text")
    nc_app.ui.files_dropdown_menu.register("test_ui_action_any", "UI TEST Any", "/ui_action_test")
    opts = webdriver.FirefoxOptions()
    opts.add_argument("--headless")
    driver = webdriver.Firefox(opts)
    try:
        driver.get(environ["NEXTCLOUD_URL"])
        driver.find_element(By.ID, "user").send_keys(environ["NC_AUTH_USER"])
        driver.find_element(By.ID, "password").send_keys(environ["NC_AUTH_PASS"])
        driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        WebDriverWait(driver, 15.0).until(exp_cond.url_contains("dashboard"))
        nc_url = environ["NEXTCLOUD_URL"]
        nc_url = nc_url.replace("index.php/", "")
        nc_url = nc_url.removesuffix("/")
        driver.get(nc_url + "/index.php/apps/files/?dir=/test_dir")
        WebDriverWait(driver, 15.0).until(exp_cond.url_contains("apps/files"))
        sleep(2.5)
        tmp_png_s = driver.find_element(By.XPATH, f'//a[contains(@href,"openfile={tmp_png.info.fileid}")]')
        items = tmp_png_s.find_elements(By.TAG_NAME, "a")
        for i in items:
            if i.accessible_name == "Actions":
                driver.execute_script("arguments[0].click();", i)
                break
        sleep(1)
        driver.find_element(By.XPATH, '//a[contains(@data-action,"test_ui_action_any")]')
        driver.find_element(By.XPATH, '//a[contains(@data-action,"test_ui_action_im")]')
        with pytest.raises(NoSuchElementException):
            driver.find_element(By.XPATH, '//a[contains(@data-action,"test_ui_action_txt")]')
    finally:
        driver.quit()
    nc_app.ui.files_dropdown_menu.unregister("test_ui_action_im")
    nc_app.ui.files_dropdown_menu.unregister("test_ui_action_txt")
    nc_app.ui.files_dropdown_menu.unregister("test_ui_action_any")


def test_unregister_ui_file_actions(nc_app):
    nc_app.ui.files_dropdown_menu.register("test_ui_action", "NcPyApi UI TEST", "/any_rel_url")
    nc_app.ui.files_dropdown_menu.unregister("test_ui_action")
    nc_app.ui.files_dropdown_menu.unregister("test_ui_action")
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.files_dropdown_menu.unregister("test_ui_action", not_fail=False)


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
            mime="",
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
        # assert fs_node.mime == fs_object.mime
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
