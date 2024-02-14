import typing
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.responses import JSONResponse

from nc_py_api import NextcloudApp, ex_app


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ex_app.set_handlers(APP, enabled_handler, default_init=False)
    yield


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(ex_app.AppAPIAuthMiddleware, disable_for=["/init"])


@APP.put("/sec_check")
def sec_check(value: int):
    print(value, flush=True)
    return JSONResponse(content={"error": ""}, status_code=200)


def init_handler_background(nc: NextcloudApp):
    nc.set_init_status(100)


@APP.post("/init")
def init_handler(
    background_tasks: BackgroundTasks,
    nc: typing.Annotated[NextcloudApp, Depends(ex_app.nc_app)],
):
    background_tasks.add_task(init_handler_background, nc)
    return JSONResponse(content={}, status_code=200)


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled_handler: enabled={enabled}", flush=True)
    if enabled:
        nc.log(ex_app.LogLvl.WARNING, f"Hello from {nc.app_cfg.app_name} :)")
    else:
        nc.log(ex_app.LogLvl.WARNING, f"Bye bye from {nc.app_cfg.app_name} :(")
    return ""


if __name__ == "__main__":
    ex_app.run_app("_install:APP", log_level="trace")
