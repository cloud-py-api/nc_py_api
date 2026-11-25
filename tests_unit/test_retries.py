"""The ``npa_retries`` option, against a local server that throttles like Nextcloud (``429``, no ``Retry-After``)."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from niquests import RetryConfiguration

from nc_py_api import (
    AsyncNextcloud,
    AsyncNextcloudApp,
    Nextcloud,
    NextcloudApp,
    NextcloudException,
)

OCS_OK = b'{"ocs": {"meta": {"status": "ok", "statuscode": 200, "message": "OK"}, "data": {}}}'
POLICY = RetryConfiguration(total=2, status_forcelist={429}, allowed_methods={"GET"}, backoff_factor=0)
USER = {"nc_auth_user": "user", "nc_auth_pass": "pass"}
APP = {"app_id": "test_app", "app_version": "1.0.0", "app_secret": "secret"}


class _Throttling(BaseHTTPRequestHandler):
    throttled = 0
    requests = 0

    def do_GET(self):  # noqa: N802
        type(self).requests += 1
        throttle = type(self).requests <= type(self).throttled
        self.send_response(429 if throttle else 200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "0" if throttle else str(len(OCS_OK)))
        self.end_headers()
        if not throttle:
            self.wfile.write(OCS_OK)

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    started = []

    def start(throttled: int):
        handler = type("Handler", (_Throttling,), {"throttled": throttled, "requests": 0})
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        started.append(httpd)
        return f"http://127.0.0.1:{httpd.server_port}", handler

    yield start
    for httpd in started:
        httpd.shutdown()


async def test_no_retries_by_default(server):
    url, handler = server(throttled=1)
    nc = AsyncNextcloud(nextcloud_url=url, **USER)
    with pytest.raises(NextcloudException) as e:
        await nc.ocs("GET", "/ocs/v1.php/cloud/capabilities")
    assert e.value.status_code == 429
    assert handler.requests == 1


def test_retry_configuration_retries_a_throttled_request(server):
    url, handler = server(throttled=2)
    nc = Nextcloud(nextcloud_url=url, npa_retries=POLICY, **USER)
    nc.ocs("GET", "/ocs/v1.php/cloud/capabilities")
    assert handler.requests == 3


async def test_retry_configuration_async(server):
    url, handler = server(throttled=2)
    nc = AsyncNextcloud(nextcloud_url=url, npa_retries=POLICY, **USER)
    await nc.ocs("GET", "/ocs/v1.php/cloud/capabilities")
    assert handler.requests == 3


async def test_retries_give_up_with_the_last_answer(server):
    url, handler = server(throttled=5)
    nc = AsyncNextcloud(
        nextcloud_url=url,
        npa_retries=RetryConfiguration(total=2, status_forcelist={429}, backoff_factor=0, raise_on_status=False),
        **USER,
    )
    with pytest.raises(NextcloudException) as e:
        await nc.ocs("GET", "/ocs/v1.php/cloud/capabilities")
    assert e.value.status_code == 429
    assert handler.requests == 3


@pytest.mark.parametrize(
    ("client", "kwargs"),
    [(Nextcloud, USER), (AsyncNextcloud, USER), (NextcloudApp, APP), (AsyncNextcloudApp, APP)],
)
def test_retries_reach_ocs_and_dav_sessions(client, kwargs):
    nc = client(nextcloud_url="http://127.0.0.1", npa_retries=4, **kwargs)
    nc._session.init_adapter_dav()  # pylint: disable=protected-access
    for adapter in (nc._session.adapter, nc._session.adapter_dav):  # pylint: disable=protected-access
        assert adapter.adapters["http://"].max_retries.total == 4
