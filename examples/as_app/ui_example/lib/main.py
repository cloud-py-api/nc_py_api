"""Example with which we test UI elements."""

import random
import typing
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, responses
from pydantic import BaseModel

from nc_py_api import NextcloudApp
from nc_py_api.ex_app import nc_app, run_app, set_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    set_handlers(APP, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    if enabled:
        nc.ui.resources.set_initial_state(
            "top_menu", "first_menu", "ui_example_state", {"initial_value": "test init value"}
        )
        nc.ui.resources.set_script("top_menu", "first_menu", "js/ui_example-main")
        nc.ui.top_menu.register("first_menu", "UI example", "img/icon.svg")
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
