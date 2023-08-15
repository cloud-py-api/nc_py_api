"""
Simplest example.
"""

from fastapi import FastAPI

from nc_py_api import NextcloudApp
from nc_py_api.ex_app import LogLvl, run_app

APP = FastAPI()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    # This will be called each time application is `enabled` or `disabled`
    # All scopes that application required already granted before this step.
    # NOTE: `user` is unavailable on this step, so all NC API calls that require it will fail as unauthorized.
    print(f"enabled={enabled}")
    if enabled:
        nc.log(LogLvl.WARNING, f"Hello from {nc.app_cfg.app_name} :)")
    else:
        nc.log(LogLvl.WARNING, f"Bye bye from {nc.app_cfg.app_name} :(")
    # In case of an error, a non-empty short string should be returned, which will be shown to the NC administrator.
    return ""


if __name__ == "__main__":
    run_app(APP, enabled_handler, "main:APP", log_level="trace")
