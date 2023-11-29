"""Example with which we test UI elements."""

import typing
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, responses

from nc_py_api import NextcloudApp
from nc_py_api.ex_app import nc_app, run_app, set_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    set_handlers(APP, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)


def enabled_handler(enabled: bool, _nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    return ""


@APP.post("/verify_initial_value")
def verify_initial_value(
    _nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
):
    # print(param)
    return responses.JSONResponse(content={"initial_value": "Button was pressed"}, status_code=200)


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
