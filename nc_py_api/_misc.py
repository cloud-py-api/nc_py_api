"""Different miscellaneous optimization/helper functions.

For internal use, prototypes can change between versions.
"""

from random import choice
from string import ascii_lowercase, ascii_uppercase, digits
from typing import Callable, Union

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


def require_capabilities(capabilities: Union[str, list[str]], srv_capabilities: dict) -> None:
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


def check_capabilities(capabilities: Union[str, list[str]], srv_capabilities: dict) -> list[str]:
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
    letters = ascii_lowercase + ascii_uppercase + digits
    return "".join(choice(letters) for _ in range(size))
