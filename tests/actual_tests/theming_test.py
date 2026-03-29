from copy import deepcopy

import pytest

from nc_py_api._theming import convert_str_color  # noqa


@pytest.mark.asyncio(scope="session")
async def test_get_theme_async(anc_any):
    theme = await anc_any.theme
    assert isinstance(theme["name"], str)
    assert isinstance(theme["url"], str)
    assert isinstance(theme["slogan"], str)


@pytest.mark.asyncio(scope="session")
async def test_convert_str_color_values_in_async(anc_any):
    theme = deepcopy(await anc_any.theme)
    for i in ("#", ""):
        theme["color"] = i
        assert convert_str_color(theme, "color") == (0, 0, 0)
    theme.pop("color")
    assert convert_str_color(theme, "color") == (0, 0, 0)
