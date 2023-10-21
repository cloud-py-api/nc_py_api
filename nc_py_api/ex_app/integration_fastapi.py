"""FastAPI directly related stuff."""

import asyncio
import hashlib
import hmac
import json
import typing

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    responses,
    status,
)

from .._misc import get_username_secret_from_headers
from ..nextcloud import NextcloudApp
from ..talk_bot import TalkBotMessage, get_bot_secret
from .misc import persistent_storage


def nc_app(request: Request) -> NextcloudApp:
    """Authentication handler for requests from Nextcloud to the application."""
    user = get_username_secret_from_headers(
        {"AUTHORIZATION-APP-API": request.headers.get("AUTHORIZATION-APP-API", "")}
    )[0]
    request_id = request.headers.get("AA-REQUEST-ID", None)
    headers = {"AA-REQUEST-ID": request_id} if request_id else {}
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
    init_handler: typing.Optional[typing.Callable[[], None]] = None,
    models_to_fetch: typing.Optional[list[str]] = None,
    models_download_params: typing.Optional[dict] = None,
):
    """Defines handlers for the application.

    :param fast_api_app: FastAPI() call return value.
    :param enabled_handler: ``Required``, callback which will be called for `enabling`/`disabling` app event.
    :param heartbeat_handler: Optional, callback that will be called for the `heartbeat` deploy event.
    :param init_handler: Optional, callback that will be called for the `init`  event.

        .. note:: If ``init_handler`` is specified, it is up to a developer to set the application init progress status.
            AppAPI will only call `enabled_handler` after it receives ``100`` as initialization status progress.

    :param models_to_fetch: Dictionary describing which models should be downloaded during `init`.

        .. note:: ```huggingface_hub`` package should be present for automatic models fetching.

    :param models_download_params: Parameters to pass to ``snapshot_download`` function from **huggingface_hub**.
    """

    def fetch_models_task(models: list[str]) -> None:
        if models:
            from huggingface_hub import snapshot_download  # noqa isort:skip pylint: disable=C0415 disable=E0401
            from tqdm import tqdm  # noqa isort:skip pylint: disable=C0415 disable=E0401

            class TqdmProgress(tqdm):
                def display(self, msg=None, pos=None):
                    if init_handler is None:
                        NextcloudApp().set_init_status(min(int((self.n * 100 / self.total) / len(models)), 100))
                    return super().display(msg, pos)

            params = models_download_params if models_download_params else {}
            if "max_workers" not in params:
                params["max_workers"] = 2
            if "cache_dir" not in params:
                params["cache_dir"] = persistent_storage()
            for model in models:
                snapshot_download(model, tqdm_class=TqdmProgress, **params)  # noqa
        if init_handler is None:
            NextcloudApp().set_init_status(100)
        else:
            init_handler()

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

    @fast_api_app.post("/init")
    def init_callback(background_tasks: BackgroundTasks):
        background_tasks.add_task(fetch_models_task, models_to_fetch if models_to_fetch else [])
        return responses.JSONResponse(content={}, status_code=200)
