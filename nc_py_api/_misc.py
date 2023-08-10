"""Different miscellaneous optimization/helper functions.

For internal use, prototypes can change between versions.
"""

from random import choice
from string import ascii_lowercase, ascii_uppercase, digits
from typing import Union

from ._exceptions import NextcloudException


def kwargs_to_dict(keys: list[str], **kwargs) -> dict:
    """Creates dictionary from ``kwargs`` by keys, the value of each is not ``None``."""
    return {k: kwargs[k] for k in keys if kwargs[k] is not None}


def require_capabilities(capabilities: Union[str, list[str]], srv_capabilities: dict) -> None:
    """Checks for capabilities and raises an exception if any of them are missing."""
    result = check_capabilities(capabilities, srv_capabilities)
    if result:
        raise NextcloudException(404, f"{result} is not available")


def check_capabilities(capabilities: Union[str, list[str]], srv_capabilities: dict) -> list[str]:
    """Checks for capabilities and returns a list of missing ones."""
    if isinstance(capabilities, str):
        capabilities = [capabilities]
    return [i for i in capabilities if i not in srv_capabilities]


def random_string(size: int) -> str:
    """Generates a random ASCII string of the given size."""
    letters = ascii_lowercase + ascii_uppercase + digits
    return "".join(choice(letters) for _ in range(size))
