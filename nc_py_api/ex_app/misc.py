"""Different miscellaneous optimization/helper functions for the Nextcloud Applications."""

import os
from sys import platform


def persistent_storage() -> str:
    """Returns the path to directory, which is permanent storage and is not deleted when the application is updated."""
    return os.getenv("APP_PERSISTENT_STORAGE", _get_app_cache_dir())


def _get_app_cache_dir() -> str:
    sys_platform = platform.lower()
    root_cache_path = (
        os.path.normpath(os.environ["LOCALAPPDATA"])
        if sys_platform == "win32"
        else (
            os.path.expanduser("~/Library/Caches")
            if sys_platform == "darwin"
            else os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        )
    )
    r = os.path.join(root_cache_path, os.environ["APP_ID"])
    os.makedirs(r, exist_ok=True)
    return r
