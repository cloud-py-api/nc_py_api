from copy import deepcopy

import pytest

from nc_py_api._theming import convert_str_color  # noqa


def test_get_theme(nc):
    theme = nc.theme
    assert isinstance(theme["name"], str)
    assert isinstance(theme["url"], str)
    assert isinstance(theme["slogan"], str)
    assert isinstance(theme["color"], tuple)
    for i in range(3):
        assert isinstance(theme["color"][i], int)
    assert isinstance(theme["color_text"], tuple)
    for i in range(3):
        assert isinstance(theme["color_text"][i], int)
    assert isinstance(theme["color_element"], tuple)
    for i in range(3):
        assert isinstance(theme["color_element"][i], int)
    assert isinstance(theme["color_element_bright"], tuple)
    for i in range(3):
        assert isinstance(theme["color_element_bright"][i], int)
    assert isinstance(theme["color_element_dark"], tuple)
    for i in range(3):
        assert isinstance(theme["color_element_dark"][i], int)
    assert isinstance(theme["logo"], str)
    assert isinstance(theme["background"], str)
    assert isinstance(theme["background_plain"], bool)
    assert isinstance(theme["background_default"], bool)


@pytest.mark.asyncio(scope="session")
async def test_get_theme_async(anc_any):
    theme = await anc_any.theme
    assert isinstance(theme["name"], str)
    assert isinstance(theme["url"], str)
    assert isinstance(theme["slogan"], str)


def test_convert_str_color_values_in(nc_any):
    theme = deepcopy(nc_any.theme)
    for i in ("#", ""):
        theme["color"] = i
        assert convert_str_color(theme, "color") == (0, 0, 0)
    theme.pop("color")
    assert convert_str_color(theme, "color") == (0, 0, 0)
