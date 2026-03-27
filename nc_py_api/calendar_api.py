"""Nextcloud Calendar DAV API."""

from ._session import NcSessionBasic

try:
    from caldav.davclient import DAVClient, DAVResponse

    class _CalendarAPI(DAVClient):
        """Class that encapsulates ``caldav.DAVClient`` to work with the Nextcloud calendar."""

        def __init__(self, session: NcSessionBasic):
            self._session = session
            super().__init__(session.cfg.dav_endpoint, enable_rfc6764=False)

        @property
        def available(self) -> bool:
            """Returns True if ``caldav`` package is avalaible, False otherwise."""
            return True

        def request(self, url, method="GET", body="", headers=None, rate_limit_time_slept=0):
            if isinstance(body, str):
                body = body.encode("UTF-8")
            if body:
                body = body.replace(b"\n", b"\r\n").replace(b"\r\r\n", b"\r\n")
            r = self._session.adapter_dav.request(
                method, url if isinstance(url, str) else str(url), data=body, headers=headers or {}
            )
            return DAVResponse(r, self)

except ImportError:

    class _CalendarAPI:  # type: ignore
        """A stub class in case **caldav** is missing."""

        def __init__(self, session: NcSessionBasic):
            self._session = session

        @property
        def available(self) -> bool:
            """Returns True if ``caldav`` package is avalaible, False otherwise."""
            return False
