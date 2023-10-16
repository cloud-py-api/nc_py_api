"""
Simplest example.
"""

from fastapi import FastAPI

from nc_py_api import NextcloudApp
from nc_py_api.ex_app import LogLvl, run_app, set_handlers

APP = FastAPI()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    # This will be called each time application is `enabled` or `disabled`
    # NOTE: `user` is unavailable on this step, so all NC API calls that require it will fail as unauthorized.
    print(f"enabled={enabled}")
    if enabled:
        nc.log(LogLvl.WARNING, f"Hello from {nc.app_cfg.app_name} :)")
    else:
        nc.log(LogLvl.WARNING, f"Bye bye from {nc.app_cfg.app_name} :(")
    # In case of an error, a non-empty short string should be returned, which will be shown to the NC administrator.
    return ""


# Of course, you can use `FastAPI lifespan: <https://fastapi.tiangolo.com/advanced/events/#lifespan>` instead of this.
# The only requirement for the application is to define `/enabled` and `/heartbeat` handlers.
@APP.on_event("startup")
def initialization():
    set_handlers(APP, enabled_handler)


if __name__ == "__main__":
    # Wrapper around `uvicorn.run`.
    # You are free to call it directly, with just using the `APP_HOST` and `APP_PORT` variables from the environment.
    run_app("main:APP", log_level="trace")
