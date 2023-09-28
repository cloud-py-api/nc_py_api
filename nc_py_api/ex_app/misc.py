"""Different miscellaneous optimization/helper functions for the Nextcloud Applications."""

import os
import typing
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


def verify_version(finalize_update: bool = True) -> typing.Optional[tuple[str, str]]:
    """Returns tuple with an old version and new version or ``None`` if there was no update taken.

    :param finalize_update: Flag indicating whether update information should be updated.
        If ``True``, all subsequent calls to this function will return that there is no update.
    """
    version_file_path = os.path.join(persistent_storage(), "_version.info")
    r = None
    with open(version_file_path, "a+t", encoding="UTF-8") as version_file:
        version_file.seek(0)
        old_version = version_file.read()
        if old_version != os.environ["APP_VERSION"]:
            r = (old_version, os.environ["APP_VERSION"])
            if finalize_update:
                version_file.seek(0)
                version_file.write(os.environ["APP_VERSION"])
                version_file.truncate()
    return r
