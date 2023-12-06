import pytest

from nc_py_api import NextcloudExceptionNotFound


def test_register_ui_top_menu(nc_app):
    nc_app.ui.top_menu.register("test_name", "Disp name", "")
    result = nc_app.ui.top_menu.get_entry("test_name")
    assert result.name == "test_name"
    assert result.display_name == "Disp name"
    assert result.icon == ""
    assert result.admin_required is False
    nc_app.ui.top_menu.unregister(result.name)
    assert nc_app.ui.top_menu.get_entry("test_name") is None
    nc_app.ui.top_menu.unregister(result.name)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.ui.top_menu.unregister(result.name, not_fail=False)
    nc_app.ui.top_menu.register("test_name", "display", "/img/test.svg", admin_required=True)
    result = nc_app.ui.top_menu.get_entry("test_name")
    assert result.name == "test_name"
    assert result.display_name == "display"
    assert result.icon == "img/test.svg"
    assert result.admin_required is True
    nc_app.ui.top_menu.register("test_name", "Display name", "", admin_required=False)
    result = nc_app.ui.top_menu.get_entry("test_name")
    assert result.name == "test_name"
    assert result.display_name == "Display name"
    assert result.icon == ""
    assert result.admin_required is False
    nc_app.ui.top_menu.unregister(result.name)
    assert nc_app.ui.top_menu.get_entry("test_name") is None
