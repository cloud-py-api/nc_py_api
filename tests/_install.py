from typing import Annotated

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


def init_handler():
    NextcloudApp().set_init_status(100)


def heartbeat_callback():
    return "ok"


@APP.on_event("startup")
def initialization():
    ex_app.set_handlers(APP, enabled_handler, heartbeat_callback, init_handler=init_handler)


if __name__ == "__main__":
    ex_app.run_app("_install:APP", log_level="trace")
