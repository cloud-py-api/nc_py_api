"""FastAPI directly related stuff."""

import asyncio
import hashlib
import hmac
import json
import typing

from fastapi import Depends, FastAPI, HTTPException, Request, responses, status

from ..nextcloud import NextcloudApp
from ..talk_bot import TalkBotMessage, get_bot_secret


def nc_app(request: Request) -> NextcloudApp:
    """Authentication handler for requests from Nextcloud to the application."""
    user = request.headers.get("NC-USER-ID", "")
    request_id = request.headers.get("AE-REQUEST-ID", None)
    headers = {"AE-REQUEST-ID": request_id} if request_id else {}
    nextcloud_app = NextcloudApp(user=user, headers=headers)
    if not nextcloud_app.request_sign_check(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return nextcloud_app


def talk_bot_app(request: Request) -> TalkBotMessage:
    """Authentication handler for bot requests from Nextcloud Talk to the application."""
    body = asyncio.run(request.body())
    secret = get_bot_secret(request.url.components.path)
    if not secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    hmac_sign = hmac.new(
        secret, request.headers.get("X-NEXTCLOUD-TALK-RANDOM", "").encode("UTF-8"), digestmod=hashlib.sha256
    )
    hmac_sign.update(body)
    if request.headers["X-NEXTCLOUD-TALK-SIGNATURE"] != hmac_sign.hexdigest():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return TalkBotMessage(json.loads(body))


def set_handlers(
    fast_api_app: FastAPI,
    enabled_handler: typing.Callable[[bool, NextcloudApp], str],
    heartbeat_handler: typing.Optional[typing.Callable[[], str]] = None,
):
    """Defines handlers for the application.

    :param fast_api_app: FastAPI() call return value.
    :param enabled_handler: ``Required``, callback which will be called for `enabling`/`disabling` app event.
    :param heartbeat_handler: Optional, callback that will be called for the `heartbeat` deploy event.
    """

    @fast_api_app.put("/enabled")
    def enabled_callback(
        enabled: bool,
        nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
    ):
        r = enabled_handler(enabled, nc)
        return responses.JSONResponse(content={"error": r}, status_code=200)

    @fast_api_app.get("/heartbeat")
    def heartbeat_callback():
        return_status = "ok"
        if heartbeat_handler is not None:
            return_status = heartbeat_handler()
        return responses.JSONResponse(content={"status": return_status}, status_code=200)
