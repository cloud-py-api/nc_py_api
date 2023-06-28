import uvicorn
from fastapi import FastAPI
import urllib3

from nc_py_api import NextcloudApp, set_enabled_handler, ApiScope, set_scopes

APP = FastAPI()


def enabled_handler(enabled: bool, _nc: NextcloudApp) -> str:
    print(f"enabled_handler: enabled={enabled}")
    return ""


@APP.on_event("startup")
def initialization():
    set_enabled_handler(APP, enabled_handler)
    set_scopes(APP, {
        "required": [ApiScope.SYSTEM, ApiScope.DAV, ApiScope.USER_INFO, ApiScope.USER_STATUS, ApiScope.NOTIFICATIONS],
        "optional": []
    })


if __name__ == "__main__":
    urllib3.disable_warnings()
    uvicorn.run("_install:APP", host="0.0.0.0", port=9002, log_level='trace', reload=False)
