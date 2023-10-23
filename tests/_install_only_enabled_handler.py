from contextlib import asynccontextmanager

from fastapi import FastAPI

from nc_py_api import NextcloudApp, ex_app


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ex_app.set_handlers(APP, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)


def enabled_handler(_enabled: bool, _nc: NextcloudApp) -> str:
    return ""


if __name__ == "__main__":
    ex_app.run_app("_install_only_enabled_handler:APP", log_level="warning")
