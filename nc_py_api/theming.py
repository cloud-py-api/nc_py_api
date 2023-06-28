"""
Nextcloud stuff for work with Theming app.
"""

from typing import TypedDict


class ThemingInfo(TypedDict):
    name: str
    url: str
    slogan: str
    color: tuple[int, int, int]
    color_text: tuple[int, int, int]
    color_element: tuple[int, int, int]
    color_element_bright: tuple[int, int, int]
    color_element_dark: tuple[int, int, int]
    logo: str
    background: str
    background_plain: bool
    background_default: bool


def __convert_str_color(theming_capability: dict, key: str) -> tuple[int, int, int]:
    if key not in theming_capability:
        return 0, 0, 0
    value = theming_capability[key]
    if not value or value == "#":
        return 0, 0, 0
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


def get_parsed_theme(theming_capability: dict) -> ThemingInfo:
    i = theming_capability
    return ThemingInfo(
        name=i["name"],
        url=i["url"],
        slogan=i["slogan"],
        color=__convert_str_color(i, "color"),
        color_text=__convert_str_color(i, "color-text"),
        color_element=__convert_str_color(i, "color-element"),
        color_element_bright=__convert_str_color(i, "color-element-bright"),
        color_element_dark=__convert_str_color(i, "color-element-dark"),
        logo=i["logo"],
        background=i.get("background", ""),
        background_plain=i.get("background-plain", False),
        background_default=i.get("background-default", False),
    )
