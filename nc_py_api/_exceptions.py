"""Exceptions for the Nextcloud API."""

from httpx import Response, codes


class NextcloudException(Exception):
    """The base exception for all Nextcloud operation errors."""

    status_code: int
    reason: str

    def __init__(self, status_code: int = 0, reason: str = "", info: str = ""):
        super(BaseException, self).__init__()
        self.status_code = status_code
        self.reason = reason
        self.info = info

    def __str__(self):
        reason = f" {self.reason}" if self.reason else ""
        info = f" <{self.info}>" if self.info else ""
        return f"[{self.status_code}]{reason}{info}"


class NextcloudExceptionNotModified(NextcloudException):
    """The exception indicates that there is no need to retransmit the requested resources."""

    def __init__(self, reason="Not modified", info: str = ""):
        super().__init__(304, reason=reason, info=info)


class NextcloudExceptionNotFound(NextcloudException):
    """The exception that is thrown during operations when the object is not found."""

    def __init__(self, reason="Not found", info: str = ""):
        super().__init__(404, reason=reason, info=info)


class NextcloudMissingCapabilities(NextcloudException):
    """The exception that is thrown when required capability for API is missing."""

    def __init__(self, reason="Missing capability", info: str = ""):
        super().__init__(412, reason=reason, info=info)


def check_error(response: Response, info: str = ""):
    """Checks HTTP code from Nextcloud, and raises exception in case of error.

    For the OCS and DAV `code` be code returned by HTTP and not the status from ``ocs_meta``.
    """
    status_code = response.status_code
    if not info:
        info = f"request: {response.request.method} {response.request.url}"
    if 996 <= status_code <= 999:
        if status_code == 996:
            phrase = "Server error"
        elif status_code == 997:
            phrase = "Unauthorised"
        elif status_code == 998:
            phrase = "Not found"
        else:
            phrase = "Unknown error"
        raise NextcloudException(status_code, reason=phrase, info=info)
    if not codes.is_error(status_code):
        return
    raise NextcloudException(status_code, reason=codes(status_code).phrase, info=info)
