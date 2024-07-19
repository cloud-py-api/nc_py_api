"""FastAPI directly related stuff."""

import asyncio
import builtins
import fnmatch
import hashlib
import json
import os
import typing
from urllib.parse import urlparse

import httpx
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    staticfiles,
    status,
)
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.requests import HTTPConnection, Request
from starlette.types import ASGIApp, Receive, Scope, Send

from .._misc import get_username_secret_from_headers
from ..nextcloud import AsyncNextcloudApp, NextcloudApp
from ..talk_bot import TalkBotMessage
from .defs import LogLvl
from .misc import persistent_storage


def nc_app(request: HTTPConnection) -> NextcloudApp:
    """Authentication handler for requests from Nextcloud to the application."""
    nextcloud_app = NextcloudApp(**__nc_app(request))
    __request_sign_check_if_needed(request, nextcloud_app)
    return nextcloud_app


def anc_app(request: HTTPConnection) -> AsyncNextcloudApp:
    """Async Authentication handler for requests from Nextcloud to the application."""
    nextcloud_app = AsyncNextcloudApp(**__nc_app(request))
    __request_sign_check_if_needed(request, nextcloud_app)
    return nextcloud_app


def talk_bot_msg(request: Request) -> TalkBotMessage:
    """Authentication handler for bot requests from Nextcloud Talk to the application."""
    return TalkBotMessage(json.loads(asyncio.run(request.body())))


async def atalk_bot_msg(request: Request) -> TalkBotMessage:
    """Async Authentication handler for bot requests from Nextcloud Talk to the application."""
    return TalkBotMessage(json.loads(await request.body()))


def set_handlers(
    fast_api_app: FastAPI,
    enabled_handler: typing.Callable[[bool, AsyncNextcloudApp | NextcloudApp], typing.Awaitable[str] | str],
    default_heartbeat: bool = True,
    default_init: bool = True,
    models_to_fetch: dict[str, dict] | None = None,
    map_app_static: bool = True,
):
    """Defines handlers for the application.

    :param fast_api_app: FastAPI() call return value.
    :param enabled_handler: ``Required``, callback which will be called for `enabling`/`disabling` app event.
    :param default_heartbeat: Set to ``False`` to disable the default `heartbeat` route handler.
    :param default_init: Set to ``False`` to disable the default `init` route handler.

        .. note:: When this parameter is ``False``, the provision of ``models_to_fetch`` is not allowed.

    :param models_to_fetch: Dictionary describing which models should be downloaded during `init`.

        .. note:: ``huggingface_hub`` package should be present for automatic models fetching.

    :param map_app_static: Should be folders ``js``, ``css``, ``l10n``, ``img`` automatically mounted in FastAPI or not.

        .. note:: First, presence of these directories in the current working dir is checked, then one directory higher.
    """
    if models_to_fetch is not None and default_init is False:
        raise ValueError("`models_to_fetch` can be defined only with `default_init`=True.")

    if asyncio.iscoroutinefunction(enabled_handler):

        @fast_api_app.put("/enabled")
        async def enabled_callback(enabled: bool, nc: typing.Annotated[AsyncNextcloudApp, Depends(anc_app)]):
            return JSONResponse(content={"error": await enabled_handler(enabled, nc)})

    else:

        @fast_api_app.put("/enabled")
        def enabled_callback(enabled: bool, nc: typing.Annotated[NextcloudApp, Depends(nc_app)]):
            return JSONResponse(content={"error": enabled_handler(enabled, nc)})

    if default_heartbeat:

        @fast_api_app.get("/heartbeat")
        async def heartbeat_callback():
            return JSONResponse(content={"status": "ok"})

    if default_init:

        @fast_api_app.post("/init")
        async def init_callback(b_tasks: BackgroundTasks, nc: typing.Annotated[NextcloudApp, Depends(nc_app)]):
            b_tasks.add_task(fetch_models_task, nc, models_to_fetch if models_to_fetch else {}, 0)
            return JSONResponse(content={})

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


def fetch_models_task(nc: NextcloudApp, models: dict[str, dict], progress_init_start_value: int) -> None:
    """Use for cases when you want to define custom `/init` but still need to easy download models."""
    if models:
        current_progress = progress_init_start_value
        percent_for_each = min(int((100 - progress_init_start_value) / len(models)), 99)
        for model in models:
            if model.startswith(("http://", "https://")):
                models[model]["path"] = __fetch_model_as_file(
                    current_progress, percent_for_each, nc, model, models[model]
                )
            else:
                models[model]["path"] = __fetch_model_as_snapshot(
                    current_progress, percent_for_each, nc, model, models[model]
                )
            current_progress += percent_for_each
    nc.set_init_status(100)


def __fetch_model_as_file(
    current_progress: int, progress_for_task: int, nc: NextcloudApp, model_path: str, download_options: dict
) -> str | None:
    result_path = download_options.pop("save_path", urlparse(model_path).path.split("/")[-1])
    try:
        with httpx.stream("GET", model_path, follow_redirects=True) as response:
            if not response.is_success:
                nc.log(LogLvl.ERROR, f"Downloading of '{model_path}' returned {response.status_code} status.")
                return None
            downloaded_size = 0
            linked_etag = ""
            for each_history in response.history:
                linked_etag = each_history.headers.get("X-Linked-ETag", "")
                if linked_etag:
                    break
            if not linked_etag:
                linked_etag = response.headers.get("X-Linked-ETag", response.headers.get("ETag", ""))
            total_size = int(response.headers.get("Content-Length"))
            try:
                existing_size = os.path.getsize(result_path)
            except OSError:
                existing_size = 0
            if linked_etag and total_size == existing_size:
                with builtins.open(result_path, "rb") as file:
                    sha256_hash = hashlib.sha256()
                    for byte_block in iter(lambda: file.read(4096), b""):
                        sha256_hash.update(byte_block)
                    if f'"{sha256_hash.hexdigest()}"' == linked_etag:
                        nc.set_init_status(min(current_progress + progress_for_task, 99))
                        return None

            with builtins.open(result_path, "wb") as file:
                last_progress = current_progress
                for chunk in response.iter_bytes(5 * 1024 * 1024):
                    downloaded_size += file.write(chunk)
                    if total_size:
                        new_progress = min(current_progress + int(progress_for_task * downloaded_size / total_size), 99)
                        if new_progress != last_progress:
                            nc.set_init_status(new_progress)
                            last_progress = new_progress

        return result_path
    except Exception as e:  # noqa pylint: disable=broad-exception-caught
        nc.log(LogLvl.ERROR, f"Downloading of '{model_path}' raised an exception: {e}")

    return None


def __fetch_model_as_snapshot(
    current_progress: int, progress_for_task, nc: NextcloudApp, mode_name: str, download_options: dict
) -> str:
    from huggingface_hub import snapshot_download  # noqa isort:skip pylint: disable=C0415 disable=E0401
    from tqdm import tqdm  # noqa isort:skip pylint: disable=C0415 disable=E0401

    class TqdmProgress(tqdm):
        def display(self, msg=None, pos=None):
            nc.set_init_status(min(current_progress + int(progress_for_task * self.n / self.total), 99))
            return super().display(msg, pos)

    workers = download_options.pop("max_workers", 2)
    cache = download_options.pop("cache_dir", persistent_storage())
    return snapshot_download(
        mode_name, tqdm_class=TqdmProgress, **download_options, max_workers=workers, cache_dir=cache
    )


def __nc_app(request: HTTPConnection) -> dict:
    user = get_username_secret_from_headers(
        {"AUTHORIZATION-APP-API": request.headers.get("AUTHORIZATION-APP-API", "")}
    )[0]
    request_id = request.headers.get("AA-REQUEST-ID", None)
    return {"user": user, "headers": {"AA-REQUEST-ID": request_id} if request_id else {}}


def __request_sign_check_if_needed(request: HTTPConnection, nextcloud_app: NextcloudApp | AsyncNextcloudApp) -> None:
    if not [i for i in getattr(request.app, "user_middleware", []) if i.cls == AppAPIAuthMiddleware]:
        _request_sign_check(request, nextcloud_app)


def _request_sign_check(request: HTTPConnection, nextcloud_app: NextcloudApp | AsyncNextcloudApp) -> str:
    try:
        return nextcloud_app._session.sign_check(request)  # noqa pylint: disable=protected-access
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from None


class AppAPIAuthMiddleware:
    """Pure ASGI AppAPIAuth Middleware."""

    _disable_for: list[str]

    def __init__(
        self,
        app: ASGIApp,
        disable_for: list[str] | None = None,
    ) -> None:
        self.app = app
        disable_for = [] if disable_for is None else [i.lstrip("/") for i in disable_for]
        self._disable_for = [i for i in disable_for if i != "heartbeat"] + ["heartbeat"]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Method that will be called by Starlette for each event."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        conn = HTTPConnection(scope)
        url_path = conn.url.path.lstrip("/")
        if not fnmatch.filter(self._disable_for, url_path):
            try:
                scope["username"] = _request_sign_check(conn, AsyncNextcloudApp())
            except HTTPException as exc:
                response = self._on_error(exc.status_code, exc.detail)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

    @staticmethod
    def _on_error(status_code: int = 400, content: str = "") -> PlainTextResponse:
        return PlainTextResponse(content, status_code=status_code)
