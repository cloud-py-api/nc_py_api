import pytest
from gfixture import NC_TO_TEST

APP_NAME = "files_trashbin"


@pytest.mark.parametrize("nc", NC_TO_TEST)
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
