"""Example with which we test UI elements."""

import typing
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, responses
from fastapi.staticfiles import StaticFiles

from nc_py_api import NextcloudApp
from nc_py_api.ex_app import nc_app, run_app, set_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    set_handlers(APP, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)
APP.mount("/static", StaticFiles(directory="static"), name="static")


def enabled_handler(enabled: bool, _nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    return ""


@APP.put("/some_endpoint")
def some_endpoint(
    param: str,
    _nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
):
    print(param)
    return responses.JSONResponse(content={"key": "some content"}, status_code=200)


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
