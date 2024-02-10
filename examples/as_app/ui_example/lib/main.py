"""Example with which we test UI elements."""

import random
import typing
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, responses
from pydantic import BaseModel

from nc_py_api import NextcloudApp
from nc_py_api.ex_app import (
    SettingsField,
    SettingsFieldType,
    SettingsForm,
    nc_app,
    run_app,
    set_handlers,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    set_handlers(APP, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)

SETTINGS_EXAMPLE = SettingsForm(
    id="settings_example",
    section_type="admin",
    section_id="ai_integration_team",
    title="AppAPI declarative settings",
    description="These fields are rendered dynamically from declarative schema",
    fields=[
        SettingsField(
            id="field1",
            title="Multi-selection",
            description="Select some option setting",
            type=SettingsFieldType.MULTI_SELECT,
            default=["foo", "bar"],
            placeholder="Select some multiple options",
            options=["foo", "bar", "baz"],
        ),
        SettingsField(
            id="some_real_setting",
            title="Choose init status check background job interval",
            description="How often AppAPI should check for initialization status",
            type=SettingsFieldType.RADIO,
            default="40m",
            placeholder="Choose init status check background job interval",
            options={
                "Each 40 minutes": "40m",
                "Each 60 minutes": "60m",
                "Each 120 minutes": "120m",
                "Each day": f"{60 * 24}m",
            },
        ),
        SettingsField(
            id="test_ex_app_field_1",
            title="Default text field",
            description="Set some simple text setting",
            type=SettingsFieldType.TEXT,
            default="foo",
            placeholder="Enter text setting",
        ),
        SettingsField(
            id="test_ex_app_field_1_1",
            title="Email field",
            description="Set email config",
            type=SettingsFieldType.EMAIL,
            default="",
            placeholder="Enter email",
        ),
        SettingsField(
            id="test_ex_app_field_1_2",
            title="Tel field",
            description="Set tel config",
            type=SettingsFieldType.TEL,
            default="",
            placeholder="Enter your tel",
        ),
        SettingsField(
            id="test_ex_app_field_1_3",
            title="Url (website) field",
            description="Set url config",
            type=SettingsFieldType.URL,
            default="",
            placeholder="Enter url",
        ),
        SettingsField(
            id="test_ex_app_field_1_4",
            title="Number field",
            description="Set number config",
            type=SettingsFieldType.NUMBER,
            default=0,
            placeholder="Enter number value",
        ),
        SettingsField(
            id="test_ex_app_field_2",
            title="Password",
            description="Set some secure value setting",
            type=SettingsFieldType.PASSWORD,
            default="",
            placeholder="Set secure value",
        ),
        SettingsField(
            id="test_ex_app_field_3",
            title="Selection",
            description="Select some option setting",
            type=SettingsFieldType.SELECT,
            default="foo",
            placeholder="Select some option setting",
            options=["foo", "bar", "baz"],
        ),
        SettingsField(
            id="test_ex_app_field_3",
            title="Selection",
            description="Select some option setting",
            type=SettingsFieldType.SELECT,
            default="foo",
            placeholder="Select some option setting",
            options=["foo", "bar", "baz"],
        ),
        SettingsField(
            id="test_ex_app_field_4",
            title="Toggle something",
            description="Select checkbox option setting",
            type=SettingsFieldType.CHECKBOX,
            default=False,
            label="Verify something if enabled",
        ),
        SettingsField(
            id="test_ex_app_field_5",
            title="Multiple checkbox toggles, describing one setting",
            description="Select checkbox option setting",
            type=SettingsFieldType.MULTI_CHECKBOX,
            default={"foo": True, "bar": True},
            options={"Foo": "foo", "Bar": "bar", "Baz": "baz", "Qux": "qux"},
        ),
        SettingsField(
            id="test_ex_app_field_6",
            title="Radio toggles, describing one setting like single select",
            description="Select radio option setting",
            type=SettingsFieldType.RADIO,
            label="Select single toggle",
            default="foo",
            options={"First radio": "foo", "Second radio": "bar", "Third radie": "baz"},
        ),
    ],
)


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    if enabled:
        nc.ui.resources.set_initial_state(
            "top_menu", "first_menu", "ui_example_state", {"initial_value": "test init value"}
        )
        nc.ui.resources.set_script("top_menu", "first_menu", "js/ui_example-main")
        nc.ui.top_menu.register("first_menu", "UI example", "img/icon.svg")
        if nc.srv_version["major"] >= 29:
            nc.ui.settings.register_form(SETTINGS_EXAMPLE)
    return ""


class Button1Format(BaseModel):
    initial_value: str


@APP.post("/verify_initial_value")
async def verify_initial_value(
    _nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
    input1: Button1Format,
):
    print("Old value: ", input1.initial_value)
    return responses.JSONResponse(content={"initial_value": str(random.randint(0, 100))}, status_code=200)


class FileInfo(BaseModel):
    getlastmodified: str
    getetag: str
    getcontenttype: str
    fileid: int
    permissions: str
    size: int
    getcontentlength: int
    favorite: int


@APP.post("/nextcloud_file")
async def nextcloud_file(
    _nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
    args: dict,
):
    print(args["file_info"])
    return responses.Response()


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
