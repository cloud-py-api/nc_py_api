"""Login flow v2 API wrapper."""

import asyncio
import json
import time
from dataclasses import dataclass

import httpx

from ._exceptions import check_error
from ._session import AsyncNcSession, NcSession

MAX_TIMEOUT = 60 * 20


@dataclass
class LoginFlow:
    """The Nextcloud Login flow v2 initialization response representation."""

    def __init__(self, raw_data: dict) -> None:
        self.raw_data = raw_data

    @property
    def login(self) -> str:
        """The URL for user authorization.

        Should be opened by the user in the default browser to authorize in Nextcloud.
        """
        return self.raw_data["login"]

    @property
    def token(self) -> str:
        """Token for a polling for confirmation of user authorization."""
        return self.raw_data["poll"]["token"]

    @property
    def endpoint(self) -> str:
        """Endpoint for polling."""
        return self.raw_data["poll"]["endpoint"]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} login_url={self.login}>"


@dataclass
class Credentials:
    """The Nextcloud Login flow v2 response with app credentials representation."""

    def __init__(self, raw_data: dict) -> None:
        self.raw_data = raw_data

    @property
    def server(self) -> str:
        """The address of Nextcloud to connect to.

        The server may specify a protocol (http or https). If no protocol is specified https will be used.
        """
        return self.raw_data["server"]

    @property
    def login_name(self) -> str:
        """The username for authenticating with Nextcloud."""
        return self.raw_data["loginName"]

    @property
    def app_password(self) -> str:
        """The application password generated for authenticating with Nextcloud."""
        return self.raw_data["appPassword"]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} login={self.login_name} app_password={self.app_password}>"


class _LoginFlowV2API:
    """Class implementing Nextcloud Login flow v2."""

    _ep_init: str = "/index.php/login/v2"
    _ep_poll: str = "/index.php/login/v2/poll"

    def __init__(self, session: NcSession) -> None:
        self._session = session

    def init(self, user_agent: str = "nc_py_api") -> LoginFlow:
        """Init a Login flow v2.

        :param user_agent: Application name. Application password will be associated with this name.
        """
        r = self._session.adapter.post(self._ep_init, headers={"user-agent": user_agent})
        return LoginFlow(_res_to_json(r))

    def poll(self, token: str, timeout: int = MAX_TIMEOUT, step: int = 1, overwrite_auth: bool = True) -> Credentials:
        """Poll the Login flow v2 credentials.

        :param token: Token for a polling for confirmation of user authorization.
        :param timeout: Maximum time to wait for polling in seconds, defaults to MAX_TIMEOUT.
        :param step: Interval for polling in seconds, defaults to 1.
        :param overwrite_auth: If True current session will be overwritten with new credentials, defaults to True.
        :raises ValueError: If timeout more than 20 minutes.
        """
        if timeout > MAX_TIMEOUT:
            msg = "Timeout can't be more than 20 minutes."
            raise ValueError(msg)
        for _ in range(timeout // step):
            r = self._session.adapter.post(self._ep_poll, data={"token": token})
            if r.status_code == 200:
                break
            time.sleep(step)
        r_model = Credentials(_res_to_json(r))
        if overwrite_auth:
            self._session.cfg.auth = (r_model.login_name, r_model.app_password)
            self._session.init_adapter(restart=True)
            self._session.init_adapter_dav(restart=True)
        return r_model


class _AsyncLoginFlowV2API:
    """Class implementing Async Nextcloud Login flow v2."""

    _ep_init: str = "/index.php/login/v2"
    _ep_poll: str = "/index.php/login/v2/poll"

    def __init__(self, session: AsyncNcSession) -> None:
        self._session = session

    async def init(self, user_agent: str = "nc_py_api") -> LoginFlow:
        """Init a Login flow v2.

        :param user_agent: Application name. Application password will be associated with this name.
        """
        r = await self._session.adapter.post(self._ep_init, headers={"user-agent": user_agent})
        return LoginFlow(_res_to_json(r))

    async def poll(
        self, token: str, timeout: int = MAX_TIMEOUT, step: int = 1, overwrite_auth: bool = True
    ) -> Credentials:
        """Poll the Login flow v2 credentials.

        :param token: Token for a polling for confirmation of user authorization.
        :param timeout: Maximum time to wait for polling in seconds, defaults to MAX_TIMEOUT.
        :param step: Interval for polling in seconds, defaults to 1.
        :param overwrite_auth: If True current session will be overwritten with new credentials, defaults to True.
        :raises ValueError: If timeout more than 20 minutes.
        """
        if timeout > MAX_TIMEOUT:
            raise ValueError("Timeout can't be more than 20 minutes.")
        for _ in range(timeout // step):
            r = await self._session.adapter.post(self._ep_poll, data={"token": token})
            if r.status_code == 200:
                break
            await asyncio.sleep(step)
        r_model = Credentials(_res_to_json(r))
        if overwrite_auth:
            self._session.cfg.auth = (r_model.login_name, r_model.app_password)
            self._session.init_adapter(restart=True)
            self._session.init_adapter_dav(restart=True)
        return r_model


def _res_to_json(response: httpx.Response) -> dict:
    check_error(response)
    return json.loads(response.text)
