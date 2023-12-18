"""FastAPI directly related stuff."""

import asyncio
import hashlib
import hmac
import json
import os
import typing

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    responses,
    staticfiles,
    status,
)

from .._misc import get_username_secret_from_headers
from ..nextcloud import AsyncNextcloudApp, NextcloudApp
from ..talk_bot import TalkBotMessage, aget_bot_secret, get_bot_secret
from .misc import persistent_storage


def nc_app(request: Request) -> NextcloudApp:
    """Authentication handler for requests from Nextcloud to the application."""
    user = get_username_secret_from_headers(
        {"AUTHORIZATION-APP-API": request.headers.get("AUTHORIZATION-APP-API", "")}
    )[0]
    request_id = request.headers.get("AA-REQUEST-ID", None)
    nextcloud_app = NextcloudApp(user=user, headers={"AA-REQUEST-ID": request_id} if request_id else {})
    if not nextcloud_app.request_sign_check(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return nextcloud_app


def anc_app(request: Request) -> AsyncNextcloudApp:
    """Async Authentication handler for requests from Nextcloud to the application."""
    user = get_username_secret_from_headers(
        {"AUTHORIZATION-APP-API": request.headers.get("AUTHORIZATION-APP-API", "")}
    )[0]
    request_id = request.headers.get("AA-REQUEST-ID", None)
    nextcloud_app = AsyncNextcloudApp(user=user, headers={"AA-REQUEST-ID": request_id} if request_id else {})
    if not nextcloud_app.request_sign_check(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return nextcloud_app


def __talk_bot_app(secret: bytes | None, request: Request, body: bytes) -> TalkBotMessage:
    if not secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    hmac_sign = hmac.new(
        secret, request.headers.get("X-NEXTCLOUD-TALK-RANDOM", "").encode("UTF-8"), digestmod=hashlib.sha256
    )
    hmac_sign.update(body)
    if request.headers["X-NEXTCLOUD-TALK-SIGNATURE"] != hmac_sign.hexdigest():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return TalkBotMessage(json.loads(body))


def talk_bot_app(request: Request) -> TalkBotMessage:
    """Authentication handler for bot requests from Nextcloud Talk to the application."""
    return __talk_bot_app(get_bot_secret(request.url.components.path), request, asyncio.run(request.body()))


async def atalk_bot_app(request: Request) -> TalkBotMessage:
    """Async Authentication handler for bot requests from Nextcloud Talk to the application."""
    return __talk_bot_app(await aget_bot_secret(request.url.components.path), request, await request.body())


def set_handlers(
    fast_api_app: FastAPI,
    enabled_handler: typing.Callable[[bool, AsyncNextcloudApp | NextcloudApp], typing.Awaitable[str] | str],
    heartbeat_handler: typing.Callable[[], typing.Awaitable[str] | str] | None = None,
    init_handler: typing.Callable[[AsyncNextcloudApp | NextcloudApp], typing.Awaitable[None] | None] | None = None,
    models_to_fetch: dict[str, dict] | None = None,
    map_app_static: bool = True,
):
    """Defines handlers for the application.

    :param fast_api_app: FastAPI() call return value.
    :param enabled_handler: ``Required``, callback which will be called for `enabling`/`disabling` app event.
    :param heartbeat_handler: Optional, callback that will be called for the `heartbeat` deploy event.
    :param init_handler: Optional, callback that will be called for the `init`  event.

        .. note:: This parameter is **mutually exclusive** with ``models_to_fetch``.

    :param models_to_fetch: Dictionary describing which models should be downloaded during `init`.

        .. note:: ```huggingface_hub`` package should be present for automatic models fetching.

    :param map_app_static: Should be folders ``js``, ``css``, ``l10n``, ``img`` automatically mounted in FastAPI or not.

        .. note:: First, presence of these directories in the current working dir is checked, then one directory higher.
    """
    if models_to_fetch is not None and init_handler is not None:
        raise ValueError("Only `init_handler` OR `models_to_fetch` can be defined.")

    if asyncio.iscoroutinefunction(enabled_handler):

        @fast_api_app.put("/enabled")
        async def enabled_callback(enabled: bool, nc: typing.Annotated[AsyncNextcloudApp, Depends(anc_app)]):
            return responses.JSONResponse(content={"error": await enabled_handler(enabled, nc)}, status_code=200)

    else:

        @fast_api_app.put("/enabled")
        def enabled_callback(enabled: bool, nc: typing.Annotated[NextcloudApp, Depends(nc_app)]):
            return responses.JSONResponse(content={"error": enabled_handler(enabled, nc)}, status_code=200)

    if heartbeat_handler is None:

        @fast_api_app.get("/heartbeat")
        async def heartbeat_callback():
            return responses.JSONResponse(content={"status": "ok"}, status_code=200)

    elif asyncio.iscoroutinefunction(heartbeat_handler):

        @fast_api_app.get("/heartbeat")
        async def heartbeat_callback():
            return responses.JSONResponse(content={"status": await heartbeat_handler()}, status_code=200)

    else:

        @fast_api_app.get("/heartbeat")
        def heartbeat_callback():
            return responses.JSONResponse(content={"status": heartbeat_handler()}, status_code=200)

    if init_handler is None:

        @fast_api_app.post("/init")
        async def init_callback(
            background_tasks: BackgroundTasks,
            nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
        ):
            background_tasks.add_task(
                __fetch_models_task,
                nc,
                models_to_fetch if models_to_fetch else {},
            )
            return responses.JSONResponse(content={}, status_code=200)

    elif asyncio.iscoroutinefunction(init_handler):

        @fast_api_app.post("/init")
        async def init_callback(
            background_tasks: BackgroundTasks,
            nc: typing.Annotated[AsyncNextcloudApp, Depends(anc_app)],
        ):
            background_tasks.add_task(init_handler, nc)
            return responses.JSONResponse(content={}, status_code=200)

    else:

        @fast_api_app.post("/init")
        def init_callback(
            background_tasks: BackgroundTasks,
            nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
        ):
            background_tasks.add_task(init_handler, nc)
            return responses.JSONResponse(content={}, status_code=200)

    if map_app_static:
        __map_app_static_folders(fast_api_app)


def __map_app_static_folders(fast_api_app: FastAPI):
    """Function to mount all necessary static folders to FastAPI."""
    for mnt_dir in ("js", "l10n", "css", "img"):
        mnt_dir_path = os.path.join(os.getcwd(), mnt_dir)
        if not os.path.exists(mnt_dir_path):
            mnt_dir_path = os.path.join(os.path.dirname(os.getcwd()), mnt_dir)
        if os.path.exists(mnt_dir_path):
            fast_api_app.mount(f"/{mnt_dir}", staticfiles.StaticFiles(directory=mnt_dir_path), name=mnt_dir)


def __fetch_models_task(
    nc: NextcloudApp,
    models: dict[str, dict],
) -> None:
    if models:
        from huggingface_hub import snapshot_download  # noqa isort:skip pylint: disable=C0415 disable=E0401
        from tqdm import tqdm  # noqa isort:skip pylint: disable=C0415 disable=E0401

        class TqdmProgress(tqdm):
            def display(self, msg=None, pos=None):
                nc.set_init_status(min(int((self.n * 100 / self.total) / len(models)), 100))
                return super().display(msg, pos)

        for model in models:
            workers = models[model].pop("max_workers", 2)
            cache = models[model].pop("cache_dir", persistent_storage())
            snapshot_download(model, tqdm_class=TqdmProgress, **models[model], max_workers=workers, cache_dir=cache)
    nc.set_init_status(100)
