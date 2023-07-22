from io import BytesIO
from os import environ
from time import sleep

import pytest
from gfixture import NC_APP
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as exp_cond
from selenium.webdriver.support.wait import WebDriverWait

from nc_py_api import NextcloudExceptionNotFound

if NC_APP is None or "app_ecosystem_v2" not in NC_APP.capabilities:
    pytest.skip("app_ecosystem_v2 is not installed.", allow_module_level=True)

if not environ["NC_AUTH_USER"] and not environ["NC_AUTH_PASS"]:
    pytest.skip("needs username & password for tests.", allow_module_level=True)


@pytest.mark.skipif(environ.get("CI", None) is not None, reason="do not work on GitHub")
def test_register_ui_file_actions():
    im = BytesIO()
    Image.linear_gradient("L").resize((768, 768)).save(im, format="PNG")
    try:
        NC_APP.files.makedirs("test_ui_action", exist_ok=True)
        NC_APP.files.upload("test_ui_action/tmp.png", bytes(im.getbuffer()))
        tmp_png = NC_APP.files.by_path("test_ui_action/tmp.png")
        NC_APP.ui_files_actions.register("test_ui_action_im", "UI TEST Image", "/ui_action_test", mime="image")
        NC_APP.ui_files_actions.register("test_ui_action_txt", "UI TEST Txt", "/ui_action_test", mime="text")
        NC_APP.ui_files_actions.register("test_ui_action_any", "UI TEST Any", "/ui_action_test")
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
            driver.get(nc_url + "/index.php/apps/files/?dir=/test_ui_action")
            WebDriverWait(driver, 15.0).until(exp_cond.url_contains("apps/files"))
            sleep(2.5)
            tmp_png_s = driver.find_element(By.XPATH, f'//a[contains(@href,"openfile={tmp_png.info["fileid"]}")]')
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
        NC_APP.ui_files_actions.unregister("test_ui_action_im")
        NC_APP.ui_files_actions.unregister("test_ui_action_txt")
        NC_APP.ui_files_actions.unregister("test_ui_action_any")
    finally:
        NC_APP.files.delete("test_ui_action", not_fail=True)


def test_unregister_ui_file_actions():
    NC_APP.ui_files_actions.register("test_ui_action", "NcPyApi UI TEST", "/any_rel_url")
    NC_APP.ui_files_actions.unregister("test_ui_action")
    NC_APP.ui_files_actions.unregister("test_ui_action")
    with pytest.raises(NextcloudExceptionNotFound):
        NC_APP.ui_files_actions.unregister("test_ui_action", not_fail=False)
