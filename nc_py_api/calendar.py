"""Nextcloud Calendar DAV API."""

from ._session import NcSessionBasic

try:
    from caldav.davclient import DAVClient, DAVResponse

    class _CalendarAPI(DAVClient):
        """Class that encapsulates ``caldav.DAVClient`` to work with the Nextcloud calendar."""

        def __init__(self, session: NcSessionBasic):
            self._session = session
            super().__init__(session.cfg.dav_endpoint)

        @property
        def available(self) -> bool:
            """Returns True if ``caldav`` package is avalaible, False otherwise."""
            return True

        def request(self, url, method="GET", body="", headers={}):  # noqa pylint: disable=dangerous-default-value
            if isinstance(body, str):
                body = body.encode("UTF-8")
            if body:
                body = body.replace(b"\n", b"\r\n").replace(b"\r\r\n", b"\r\n")
            r = self._session.adapter_dav.request(
                method, url if isinstance(url, str) else str(url), content=body, headers=headers
            )
            return DAVResponse(r)

except ImportError:

    class _CalendarAPI:  # type: ignore
        """A stub class in case **caldav** is missing."""

        def __init__(self, session: NcSessionBasic):
            self._session = session

        @property
        def available(self) -> bool:
            """Returns True if ``caldav`` package is avalaible, False otherwise."""
            return False
