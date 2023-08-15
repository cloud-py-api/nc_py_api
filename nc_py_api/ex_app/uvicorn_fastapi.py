"""Uvicorn wrappers to run the external application."""
import typing
from os import environ

from uvicorn import run
from uvicorn.config import ASGIApplication


def run_app(
    uvicorn_app: typing.Union["ASGIApplication", typing.Callable, str],
    *args,
    **kwargs,
) -> None:
    """Wrapper around Uvicorn's ``run`` function.

    Accepts and passes all arguments to it, except for ``host`` and ``port`` which are taken from the environment.
    """
    run(uvicorn_app, *args, host=environ.get("APP_HOST", "127.0.0.1"), port=int(environ["APP_PORT"]), **kwargs)
