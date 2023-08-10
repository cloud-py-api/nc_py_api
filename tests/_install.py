from os import environ
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from nc_py_api import NextcloudApp, ex_app

APP = FastAPI()


@APP.put("/sec_check")
def sec_check(
    value: int,
    nc: Annotated[NextcloudApp, Depends(ex_app.nc_app)],
):
    print(value)
    _ = nc
    return JSONResponse(content={"error": ""}, status_code=200)


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled_handler: enabled={enabled}", flush=True)
    if enabled:
        nc.log(ex_app.LogLvl.WARNING, f"Hello from {nc.app_cfg.app_name} :)")
    else:
        nc.log(ex_app.LogLvl.WARNING, f"Bye bye from {nc.app_cfg.app_name} :(")
    return ""


def heartbeat_callback():
    return "ok"


@APP.on_event("startup")
def initialization():
    ex_app.set_enabled_handler(APP, enabled_handler)
    ex_app.set_scopes(
        APP,
        {
            "required": [
                ex_app.ApiScope.SYSTEM,
                ex_app.ApiScope.DAV,
                ex_app.ApiScope.USER_INFO,
                ex_app.ApiScope.USER_STATUS,
                ex_app.ApiScope.NOTIFICATIONS,
                ex_app.ApiScope.WEATHER_STATUS,
                ex_app.ApiScope.FILES_SHARING,
            ],
            "optional": [],
        },
    )
    ex_app.enable_heartbeat(APP, heartbeat_callback)


if __name__ == "__main__":
    uvicorn.run(
        "_install:APP", host=environ.get("APP_HOST", "127.0.0.1"), port=int(environ["APP_PORT"]), log_level="trace"
    )
