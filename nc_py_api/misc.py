"""
Different miscellaneous optimization/helper functions.

For internal use, prototypes can change between versions.
"""

from typing import Union

from .exceptions import NextcloudException


def kwargs_to_dict(keys: list[str], **kwargs) -> dict:
    # return {k: kwargs[k] for k in keys if kwargs[k] is not None}
    data = {}
    for k in keys:
        if kwargs[k] is not None:
            data[k] = kwargs[k]
    return data


def require_capabilities(capabilities: Union[str, list[str]], srv_capabilities: dict) -> None:
    result = check_capabilities(capabilities, srv_capabilities)
    if result:
        raise NextcloudException(404, f"{result} is not available")


def check_capabilities(capabilities: Union[str, list[str]], srv_capabilities: dict) -> list[str]:
    if isinstance(capabilities, str):
        capabilities = [capabilities]
    return [i for i in capabilities if i not in srv_capabilities]
