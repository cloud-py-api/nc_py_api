from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from nc_py_api import AsyncNextcloudApp, ex_app


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ex_app.set_handlers(APP, enabled_handler, heartbeat_callback, init_handler=init_handler)
    yield


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(ex_app.AppAPIAuthMiddleware)


@APP.put("/sec_check")
async def sec_check(
    value: int,
):
    print(value, flush=True)
    return JSONResponse(content={"error": ""}, status_code=200)


async def enabled_handler(enabled: bool, nc: AsyncNextcloudApp) -> str:
    print(f"enabled_handler: enabled={enabled}", flush=True)
    if enabled:
        await nc.log(ex_app.LogLvl.WARNING, f"Hello from {nc.app_cfg.app_name} :)")
    else:
        await nc.log(ex_app.LogLvl.WARNING, f"Bye bye from {nc.app_cfg.app_name} :(")
    return ""


async def init_handler(nc: AsyncNextcloudApp):
    await nc.set_init_status(100)


async def heartbeat_callback():
    return "ok"


if __name__ == "__main__":
    ex_app.run_app("_install_async:APP", log_level="trace")
