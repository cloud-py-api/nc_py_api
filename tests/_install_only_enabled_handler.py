from os import environ

import uvicorn
from fastapi import FastAPI

from nc_py_api import NextcloudApp, ex_app

APP = FastAPI()


def enabled_handler(_enabled: bool, _nc: NextcloudApp) -> str:
    return ""


@APP.on_event("startup")
def initialization():
    ex_app.set_enabled_handler(APP, enabled_handler)


if __name__ == "__main__":
    uvicorn.run(
        "_install:APP",
        host=environ.get("APP_HOST", "127.0.0.1"),
        port=int(environ.get("APP_PORT", 9009)),
    )
