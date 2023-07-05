"""
Directly related stuff to FastAPI.
"""

from typing import Annotated, Callable, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from .constants import ApiScopesStruct
from .nextcloud import NextcloudApp


def nc_app(request: Request) -> NextcloudApp:
    user = request.headers.get("NC-USER-ID", "")
    request_id = request.headers.get("AE-REQUEST-ID", None)
    headers = {"AE-REQUEST-ID": request_id} if request_id else {}
    nextcloud_app = NextcloudApp(user=user, headers=headers)
    if not nextcloud_app.request_sign_check(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return nextcloud_app


def set_scopes(fast_api_app: FastAPI, desired_scopes: ApiScopesStruct):
    @fast_api_app.get("/scopes")
    def scopes_handler(
        _nc: Annotated[NextcloudApp, Depends(nc_app)],
    ):
        return JSONResponse(content=desired_scopes, status_code=200)


def set_enabled_handler(fast_api_app: FastAPI, callback: Callable[[bool, NextcloudApp], str]):
    @fast_api_app.put("/enabled")
    def enabled_handler(
        enabled: bool,
        nc: Annotated[NextcloudApp, Depends(nc_app)],
    ):
        r = callback(enabled, nc)
        return JSONResponse(content={"error": r}, status_code=200)


def enable_heartbeat(fast_api_app: FastAPI, callback: Optional[Callable[[], str]] = None):
    @fast_api_app.get("/heartbeat")
    def heartbeat_handler():
        return_status = "ok"
        if callback is not None:
            return_status = callback()
        return JSONResponse(content={"status": return_status}, status_code=200)
