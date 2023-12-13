"""Uvicorn wrappers to run the external application."""

import typing
from os import environ

try:
    import uvicorn
except ImportError as ex:
    from .._deffered_error import DeferredError

    uvicorn = DeferredError(ex)


def run_app(
    uvicorn_app: typing.Callable | str | typing.Any,
    *args,
    **kwargs,
) -> None:
    """Wrapper around Uvicorn's ``run`` function.

    :param uvicorn_app: "ASGIApplication", usually consists of the "name_of_file:FastAPI_class".
    :param args: Any args to pass to **uvicorn.run**.
    :param kwargs: Any **kwargs** to pass to **uvicorn.run**, except ``host`` and ``port``.
    """
    uvicorn.run(uvicorn_app, *args, host=environ.get("APP_HOST", "127.0.0.1"), port=int(environ["APP_PORT"]), **kwargs)
