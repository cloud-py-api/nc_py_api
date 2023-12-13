"""Different miscellaneous optimization/helper functions.

For internal use, prototypes can change between versions.
"""

import secrets
from base64 import b64decode
from collections.abc import Callable
from datetime import datetime, timezone
from string import ascii_letters, digits

from ._exceptions import NextcloudMissingCapabilities


def __check_for_none(v):
    return v is not None


def kwargs_to_params(keys: list[str], filter_func: Callable = __check_for_none, **kwargs) -> dict:
    """Returns dictionary from ``kwargs`` by keys. By default, only pairs with ``not None`` values returned."""
    return {k: kwargs[k] for k in keys if filter_func(kwargs[k])}


def clear_from_params_empty(keys: list[str], params: dict) -> None:
    """Removes key:values pairs from ``params`` which values are empty."""
    for key in keys:
        if key in params and not params[key]:
            params.pop(key)


def require_capabilities(capabilities: str | list[str], srv_capabilities: dict) -> None:
    """Checks for capabilities and raises an exception if any of them are missing."""
    result = check_capabilities(capabilities, srv_capabilities)
    if result:
        raise NextcloudMissingCapabilities(info=str(result))


def __check_sub_capability(split_capabilities: list[str], srv_capabilities: dict) -> bool:
    """Returns ``True`` if such capability is present and **enabled**."""
    n_split_capabilities = len(split_capabilities)
    capabilities_nesting = srv_capabilities
    for i, v in enumerate(split_capabilities):
        if i != 0 and i == n_split_capabilities - 1:
            return (
                bool(capabilities_nesting.get(v, False))
                if isinstance(capabilities_nesting, dict)
                else bool(v in capabilities_nesting)
            )
        if v not in capabilities_nesting:
            return False
        capabilities_nesting = capabilities_nesting[v]
    return True


def check_capabilities(capabilities: str | list[str], srv_capabilities: dict) -> list[str]:
    """Checks for capabilities and returns a list of missing ones."""
    if isinstance(capabilities, str):
        capabilities = [capabilities]
    missing_capabilities = []
    for capability in capabilities:
        split_capabilities = capability.split(".")
        if not __check_sub_capability(split_capabilities, srv_capabilities):
            missing_capabilities.append(capability)
    return missing_capabilities


def random_string(size: int) -> str:
    """Generates a random ASCII string of the given size."""
    char_string = ascii_letters + digits
    return "".join(secrets.choice(char_string) for _ in range(size))


def nc_iso_time_to_datetime(iso8601_time: str) -> datetime:
    """Returns parsed ``datetime`` or datetime(1970, 1, 1) in case of error."""
    try:
        return datetime.fromisoformat(iso8601_time)
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def get_username_secret_from_headers(headers: dict) -> tuple[str, str]:
    """Returns tuple with ``username`` and ``app_secret`` from headers."""
    auth_aa = b64decode(headers.get("AUTHORIZATION-APP-API", "")).decode("UTF-8")
    try:
        username, app_secret = auth_aa.split(":", maxsplit=1)
    except ValueError:
        return "", ""
    return username, app_secret
