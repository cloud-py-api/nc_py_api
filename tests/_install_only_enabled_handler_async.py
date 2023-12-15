from contextlib import asynccontextmanager

from fastapi import FastAPI

from nc_py_api import AsyncNextcloudApp, ex_app


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ex_app.set_handlers(APP, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)


async def enabled_handler(_enabled: bool, _nc: AsyncNextcloudApp) -> str:
    return ""


if __name__ == "__main__":
    ex_app.run_app("_install_only_enabled_handler_async:APP", log_level="warning")
