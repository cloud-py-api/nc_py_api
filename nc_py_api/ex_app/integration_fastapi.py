"""FastAPI directly related stuff."""

from typing import Annotated, Callable, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ..nextcloud import NextcloudApp


def nc_app(request: Request) -> NextcloudApp:
    """Authentication handler for requests from Nextcloud to the application."""
    user = request.headers.get("NC-USER-ID", "")
    request_id = request.headers.get("AE-REQUEST-ID", None)
    headers = {"AE-REQUEST-ID": request_id} if request_id else {}
    nextcloud_app = NextcloudApp(user=user, headers=headers)
    if not nextcloud_app.request_sign_check(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return nextcloud_app


def set_handlers(
    fast_api_app: FastAPI,
    enabled_handler: Callable[[bool, NextcloudApp], str],
    heartbeat_handler: Optional[Callable[[], str]] = None,
):
    """Defines handlers for the application.

    :param fast_api_app: FastAPI() call return value.
    :param enabled_handler: ``Required``, callback which will be called for `enabling`/`disabling` app event.
    :param heartbeat_handler: Optional, callback that will be called for the `heartbeat` deploy event.
    """

    @fast_api_app.put("/enabled")
    def enabled_callback(
        enabled: bool,
        nc: Annotated[NextcloudApp, Depends(nc_app)],
    ):
        r = enabled_handler(enabled, nc)
        return JSONResponse(content={"error": r}, status_code=200)

    @fast_api_app.get("/heartbeat")
    def heartbeat_callback():
        return_status = "ok"
        if heartbeat_handler is not None:
            return_status = heartbeat_handler()
        return JSONResponse(content={"status": return_status}, status_code=200)
