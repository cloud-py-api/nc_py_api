import pytest

from nc_py_api import NextcloudExceptionNotFound


def test_initial_state(nc_app):
    nc_app.ui.resources.delete_initial_state("top_menu", "some_page", "some_key")
    assert nc_app.ui.resources.get_initial_state("top_menu", "some_page", "some_key") is None
    nc_app.ui.resources.set_initial_state("top_menu", "some_page", "some_key", {"k1": 1, "k2": 2})
    r = nc_app.ui.resources.get_initial_state("top_menu", "some_page", "some_key")
    assert r.appid == nc_app.app_cfg.app_name
    assert r.name == "some_page"
    assert r.key == "some_key"
    assert r.value == {"k1": 1, "k2": 2}
    nc_app.ui.resources.set_initial_state("top_menu", "some_page", "some_key", {"k1": "v1"})
    r = nc_app.ui.resources.get_initial_state("top_menu", "some_page", "some_key")
    assert r.value == {"k1": "v1"}
    assert str(r).find("key=some_key")
    nc_app.ui.resources.delete_initial_state("top_menu", "some_page", "some_key", not_fail=False)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.resources.delete_initial_state("top_menu", "some_page", "some_key", not_fail=False)


def test_initial_states(nc_app):
    nc_app.ui.resources.set_initial_state("top_menu", "some_page", "key1", [])
    nc_app.ui.resources.set_initial_state("top_menu", "some_page", "key2", {"k2": "v2"})
    r1 = nc_app.ui.resources.get_initial_state("top_menu", "some_page", "key1")
    r2 = nc_app.ui.resources.get_initial_state("top_menu", "some_page", "key2")
    assert r1.key == "key1"
    assert r1.value == []
    assert r2.key == "key2"
    assert r2.value == {"k2": "v2"}
    nc_app.ui.resources.delete_initial_state("top_menu", "some_page", "key1", not_fail=False)
    nc_app.ui.resources.delete_initial_state("top_menu", "some_page", "key2", not_fail=False)


def test_script(nc_app):
    nc_app.ui.resources.delete_script("top_menu", "some_page", "js/some_script")
    assert nc_app.ui.resources.get_script("top_menu", "some_page", "js/some_script") is None
    nc_app.ui.resources.set_script("top_menu", "some_page", "js/some_script")
    r = nc_app.ui.resources.get_script("top_menu", "some_page", "js/some_script")
    assert r.appid == nc_app.app_cfg.app_name
    assert r.name == "some_page"
    assert r.path == "js/some_script"
    assert r.after_app_id == ""
    nc_app.ui.resources.set_script("top_menu", "some_page", "js/some_script", "core")
    r = nc_app.ui.resources.get_script("top_menu", "some_page", "js/some_script")
    assert r.path == "js/some_script"
    assert r.after_app_id == "core"
    assert str(r).find("path=js/some_script")
    nc_app.ui.resources.delete_script("top_menu", "some_page", "js/some_script", not_fail=False)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.resources.delete_script("top_menu", "some_page", "js/some_script", not_fail=False)


def test_scripts(nc_app):
    nc_app.ui.resources.set_script("top_menu", "some_page", "js/script1")
    nc_app.ui.resources.set_script("top_menu", "some_page", "js/script2", "core")
    r1 = nc_app.ui.resources.get_script("top_menu", "some_page", "js/script1")
    r2 = nc_app.ui.resources.get_script("top_menu", "some_page", "js/script2")
    assert r1.path == "js/script1"
    assert r1.after_app_id == ""
    assert r2.path == "js/script2"
    assert r2.after_app_id == "core"
    nc_app.ui.resources.delete_script("top_menu", "some_page", "js/script1", not_fail=False)
    nc_app.ui.resources.delete_script("top_menu", "some_page", "js/script2", not_fail=False)


def test_scripts_slash(nc_app):
    nc_app.ui.resources.set_script("top_menu", "test_slash", "/js/script1")
    r = nc_app.ui.resources.get_script("top_menu", "test_slash", "/js/script1")
    assert r == nc_app.ui.resources.get_script("top_menu", "test_slash", "js/script1")
    assert r.path == "js/script1"
    nc_app.ui.resources.delete_script("top_menu", "test_slash", "/js/script1", not_fail=False)
    assert nc_app.ui.resources.get_script("top_menu", "test_slash", "js/script1") is None
    assert nc_app.ui.resources.get_script("top_menu", "test_slash", "/js/script1") is None
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.resources.delete_script("top_menu", "test_slash", "/js/script1", not_fail=False)


def test_style(nc_app):
    nc_app.ui.resources.delete_style("top_menu", "some_page", "css/some_path")
    assert nc_app.ui.resources.get_style("top_menu", "some_page", "css/some_path") is None
    nc_app.ui.resources.set_style("top_menu", "some_page", "css/some_path")
    r = nc_app.ui.resources.get_style("top_menu", "some_page", "css/some_path")
    assert r.appid == nc_app.app_cfg.app_name
    assert r.name == "some_page"
    assert r.path == "css/some_path"
    assert str(r).find("path=css/some_path")
    nc_app.ui.resources.delete_style("top_menu", "some_page", "css/some_path", not_fail=False)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.resources.delete_style("top_menu", "some_page", "css/some_path", not_fail=False)


def test_styles(nc_app):
    nc_app.ui.resources.set_style("top_menu", "some_page", "css/style1")
    nc_app.ui.resources.set_style("top_menu", "some_page", "css/style2")
    r1 = nc_app.ui.resources.get_style("top_menu", "some_page", "css/style1")
    r2 = nc_app.ui.resources.get_style("top_menu", "some_page", "css/style2")
    assert r1.path == "css/style1"
    assert r2.path == "css/style2"
    nc_app.ui.resources.delete_style("top_menu", "some_page", "css/style1", not_fail=False)
    nc_app.ui.resources.delete_style("top_menu", "some_page", "css/style2", not_fail=False)


def test_styles_slash(nc_app):
    nc_app.ui.resources.set_style("top_menu", "test_slash", "/js/script1")
    r = nc_app.ui.resources.get_style("top_menu", "test_slash", "/js/script1")
    assert r == nc_app.ui.resources.get_style("top_menu", "test_slash", "js/script1")
    assert r.path == "js/script1"
    nc_app.ui.resources.delete_style("top_menu", "test_slash", "/js/script1", not_fail=False)
    assert nc_app.ui.resources.get_style("top_menu", "test_slash", "js/script1") is None
    assert nc_app.ui.resources.get_style("top_menu", "test_slash", "/js/script1") is None
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.resources.delete_style("top_menu", "test_slash", "/js/script1", not_fail=False)
