"""Uvicorn wrappers to run the external application."""
import typing
from os import environ

from fastapi import FastAPI
from uvicorn import run
from uvicorn.config import ASGIApplication

from ..nextcloud import NextcloudApp
from .integration_fastapi import enable_heartbeat, set_enabled_handler


def run_app(
    fast_api_app: FastAPI,
    enabled_handler: typing.Callable[[bool, NextcloudApp], str],
    uvicorn_app: typing.Union["ASGIApplication", typing.Callable, str],
    heartbeat_handler: typing.Optional[typing.Callable[[], str]] = None,
    **kwargs,
) -> None:
    """Runs the application."""

    @fast_api_app.on_event("startup")
    def initialization():
        set_enabled_handler(fast_api_app, enabled_handler)
        enable_heartbeat(fast_api_app, heartbeat_handler)

    run(uvicorn_app, host=environ.get("APP_HOST", "127.0.0.1"), port=int(environ["APP_PORT"]), **kwargs)
