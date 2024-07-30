"""Session represents one connection to Nextcloud. All related stuff for these live here."""

import builtins
import pathlib
import re
import typing
from abc import ABC, abstractmethod
from base64 import b64encode
from dataclasses import dataclass
from enum import IntEnum
from json import loads
from os import environ

from httpx import AsyncClient, Client, Headers, Limits, ReadTimeout, Request, Response
from starlette.requests import HTTPConnection

from . import options
from ._exceptions import (
    NextcloudException,
    NextcloudExceptionNotFound,
    NextcloudExceptionNotModified,
    check_error,
)
from ._misc import get_username_secret_from_headers


class OCSRespond(IntEnum):
    """Special Nextcloud respond statuses for OCS calls."""

    RESPOND_SERVER_ERROR = 996
    RESPOND_UNAUTHORISED = 997
    RESPOND_NOT_FOUND = 998
    RESPOND_UNKNOWN_ERROR = 999


class ServerVersion(typing.TypedDict):
    """Nextcloud version information."""

    major: int
    """Major version"""
    minor: int
    """Minor version"""
    micro: int
    """Micro version"""
    string: str
    """Full version in string format"""
    extended_support: bool
    """Indicates if the subscription has extended support"""


@dataclass
class RuntimeOptions:
    xdebug_session: str
    timeout: int | None
    timeout_dav: int | None
    _nc_cert: str | bool
    upload_chunk_v2: bool

    def __init__(self, **kwargs):
        self.xdebug_session = kwargs.get("xdebug_session", options.XDEBUG_SESSION)
        self.timeout = kwargs.get("npa_timeout", options.NPA_TIMEOUT)
        self.timeout_dav = kwargs.get("npa_timeout_dav", options.NPA_TIMEOUT_DAV)
        self._nc_cert = kwargs.get("npa_nc_cert", options.NPA_NC_CERT)
        self.upload_chunk_v2 = kwargs.get("chunked_upload_v2", options.CHUNKED_UPLOAD_V2)

    @property
    def nc_cert(self) -> str | bool:
        return self._nc_cert


@dataclass
class BasicConfig:
    endpoint: str
    dav_endpoint: str
    dav_url_suffix: str
    options: RuntimeOptions

    def __init__(self, **kwargs):
        full_nc_url = self._get_config_value("nextcloud_url", **kwargs)
        self.endpoint = full_nc_url.removesuffix("/index.php").removesuffix("/")
        self.dav_url_suffix = self._get_config_value("dav_url_suffix", raise_not_found=False, **kwargs)
        if not self.dav_url_suffix:
            self.dav_url_suffix = "remote.php/dav"
        self.dav_url_suffix = "/" + self.dav_url_suffix.strip("/")
        self.dav_endpoint = self.endpoint + self.dav_url_suffix
        self.options = RuntimeOptions(**kwargs)

    @staticmethod
    def _get_config_value(value_name: str, raise_not_found=True, **kwargs):
        if value_name in kwargs:
            return kwargs[value_name]
        value_name_upper = value_name.upper()
        if value_name_upper in environ:
            return environ[value_name_upper]
        if raise_not_found:
            raise ValueError(f"`{value_name}` is not found.")
        return None


@dataclass
class Config(BasicConfig):
    auth: tuple[str, str] = ("", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        nc_auth_user = self._get_config_value("nc_auth_user", raise_not_found=False, **kwargs)
        nc_auth_pass = self._get_config_value("nc_auth_pass", raise_not_found=False, **kwargs)
        if nc_auth_user and nc_auth_pass:
            self.auth = (nc_auth_user, nc_auth_pass)


@dataclass
class AppConfig(BasicConfig):
    """Application configuration."""

    aa_version: str
    """AppAPI version"""
    app_name: str
    """Application ID"""
    app_version: str
    """Application version"""
    app_secret: str
    """Application authentication secret"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aa_version = self._get_config_value("aa_version", raise_not_found=False, **kwargs)
        if not self.aa_version:
            self.aa_version = "2.2.0"
        self.app_name = self._get_config_value("app_id", **kwargs)
        self.app_version = self._get_config_value("app_version", **kwargs)
        self.app_secret = self._get_config_value("app_secret", **kwargs)


class NcSessionBase(ABC):
    adapter: AsyncClient | Client
    adapter_dav: AsyncClient | Client
    cfg: BasicConfig
    custom_headers: dict
    response_headers: Headers
    _user: str
    _capabilities: dict

    @abstractmethod
    def __init__(self, **kwargs):
        self._capabilities = {}
        self._user = kwargs.get("user", "")
        self.custom_headers = kwargs.get("headers", {})
        self.limits = Limits(max_keepalive_connections=20, max_connections=20, keepalive_expiry=60.0)
        self.init_adapter()
        self.init_adapter_dav()
        self.response_headers = Headers()
        self._ocs_regexp = re.compile(r"/ocs/v[12]\.php/|/apps/groupfolders/")

    def init_adapter(self, restart=False) -> None:
        if getattr(self, "adapter", None) is None or restart:
            self.adapter = self._create_adapter()
            self.adapter.headers.update({"OCS-APIRequest": "true"})
            if self.custom_headers:
                self.adapter.headers.update(self.custom_headers)
            if options.XDEBUG_SESSION:
                self.adapter.cookies.set("XDEBUG_SESSION", options.XDEBUG_SESSION)
            self._capabilities = {}

    def init_adapter_dav(self, restart=False) -> None:
        if getattr(self, "adapter_dav", None) is None or restart:
            self.adapter_dav = self._create_adapter(dav=True)
            if self.custom_headers:
                self.adapter_dav.headers.update(self.custom_headers)
            if options.XDEBUG_SESSION:
                self.adapter_dav.cookies.set("XDEBUG_SESSION", options.XDEBUG_SESSION)

    @abstractmethod
    def _create_adapter(self, dav: bool = False) -> AsyncClient | Client:
        pass  # pragma: no cover

    @property
    def ae_url(self) -> str:
        """Return base url for the AppAPI endpoints."""
        return "/ocs/v1.php/apps/app_api/api/v1"

    @property
    def ae_url_v2(self) -> str:
        """Return base url for the AppAPI endpoints(version 2)."""
        return "/ocs/v1.php/apps/app_api/api/v2"


class NcSessionBasic(NcSessionBase, ABC):
    adapter: Client
    adapter_dav: Client

    def ocs(
        self,
        method: str,
        path: str,
        *,
        content: bytes | str | typing.Iterable[bytes] | typing.AsyncIterable[bytes] | None = None,
        json: dict | list | None = None,
        params: dict | None = None,
        files: dict | None = None,
        **kwargs,
    ):
        self.init_adapter()
        info = f"request: {method} {path}"
        nested_req = kwargs.pop("nested_req", False)
        try:
            response = self.adapter.request(
                method, path, content=content, json=json, params=params, files=files, **kwargs
            )
        except ReadTimeout:
            raise NextcloudException(408, info=info) from None

        check_error(response, info)
        if response.status_code == 204:  # NO_CONTENT
            return []
        response_data = loads(response.text)
        ocs_meta = response_data["ocs"]["meta"]
        if ocs_meta["status"] != "ok":
            if (
                not nested_req
                and ocs_meta["statuscode"] == 403
                and str(ocs_meta["message"]).lower().find("password confirmation is required") != -1
            ):
                self.adapter.close()
                self.init_adapter(restart=True)
                return self.ocs(method, path, **kwargs, content=content, json=json, params=params, nested_req=True)
            if ocs_meta["statuscode"] in (404, OCSRespond.RESPOND_NOT_FOUND):
                raise NextcloudExceptionNotFound(reason=ocs_meta["message"], info=info)
            if ocs_meta["statuscode"] == 304:
                raise NextcloudExceptionNotModified(reason=ocs_meta["message"], info=info)
            raise NextcloudException(status_code=ocs_meta["statuscode"], reason=ocs_meta["message"], info=info)
        return response_data["ocs"]["data"]

    def update_server_info(self) -> None:
        self._capabilities = self.ocs("GET", "/ocs/v1.php/cloud/capabilities")

    @property
    def capabilities(self) -> dict:
        if not self._capabilities:
            self.update_server_info()
        return self._capabilities["capabilities"]

    @property
    def nc_version(self) -> ServerVersion:
        if not self._capabilities:
            self.update_server_info()
        v = self._capabilities["version"]
        return ServerVersion(
            major=v["major"],
            minor=v["minor"],
            micro=v["micro"],
            string=v["string"],
            extended_support=v["extendedSupport"],
        )

    @property
    def user(self) -> str:
        """Current user ID. Can be different from the login name."""
        if isinstance(self, NcSession) and not self._user:  # do not trigger for NextcloudApp
            self._user = self.ocs("GET", "/ocs/v1.php/cloud/user")["id"]
        return self._user

    def set_user(self, user_id: str) -> None:
        self._user = user_id

    def download2stream(self, url_path: str, fp, dav: bool = False, **kwargs):
        if isinstance(fp, str | pathlib.Path):
            with builtins.open(fp, "wb") as f:
                self.download2fp(url_path, f, dav, **kwargs)
        elif hasattr(fp, "write"):
            self.download2fp(url_path, fp, dav, **kwargs)
        else:
            raise TypeError("`fp` must be a path to file or an object with `write` method.")

    def _get_adapter_kwargs(self, dav: bool) -> dict[str, typing.Any]:
        if dav:
            return {
                "base_url": self.cfg.dav_endpoint,
                "timeout": self.cfg.options.timeout_dav,
                "event_hooks": {"request": [], "response": [self._response_event]},
            }
        return {
            "base_url": self.cfg.endpoint,
            "timeout": self.cfg.options.timeout,
            "event_hooks": {"request": [self._request_event_ocs], "response": [self._response_event]},
        }

    def _request_event_ocs(self, request: Request) -> None:
        str_url = str(request.url)
        if re.search(self._ocs_regexp, str_url) is not None:  # this is OCS call
            request.url = request.url.copy_merge_params({"format": "json"})
            request.headers["Accept"] = "application/json"

    def _response_event(self, response: Response) -> None:
        str_url = str(response.request.url)
        # we do not want ResponseHeaders for those two endpoints, as call to them can occur during DAV calls.
        for i in ("/ocs/v1.php/cloud/capabilities?format=json", "/ocs/v1.php/cloud/user?format=json"):
            if str_url.endswith(i):
                return
        self.response_headers = response.headers

    def download2fp(self, url_path: str, fp, dav: bool, params=None, **kwargs):
        adapter = self.adapter_dav if dav else self.adapter
        with adapter.stream("GET", url_path, params=params) as response:
            check_error(response)
            for data_chunk in response.iter_raw(chunk_size=kwargs.get("chunk_size", 5 * 1024 * 1024)):
                fp.write(data_chunk)


class AsyncNcSessionBasic(NcSessionBase, ABC):
    adapter: AsyncClient
    adapter_dav: AsyncClient

    async def ocs(
        self,
        method: str,
        path: str,
        *,
        content: bytes | str | typing.Iterable[bytes] | typing.AsyncIterable[bytes] | None = None,
        json: dict | list | None = None,
        params: dict | None = None,
        files: dict | None = None,
        **kwargs,
    ):
        self.init_adapter()
        info = f"request: {method} {path}"
        nested_req = kwargs.pop("nested_req", False)
        try:
            response = await self.adapter.request(
                method, path, content=content, json=json, params=params, files=files, **kwargs
            )
        except ReadTimeout:
            raise NextcloudException(408, info=info) from None

        check_error(response, info)
        if response.status_code == 204:  # NO_CONTENT
            return []
        response_data = loads(response.text)
        ocs_meta = response_data["ocs"]["meta"]
        if ocs_meta["status"] != "ok":
            if (
                not nested_req
                and ocs_meta["statuscode"] == 403
                and str(ocs_meta["message"]).lower().find("password confirmation is required") != -1
            ):
                await self.adapter.aclose()
                self.init_adapter(restart=True)
                return await self.ocs(
                    method, path, **kwargs, content=content, json=json, params=params, nested_req=True
                )
            if ocs_meta["statuscode"] in (404, OCSRespond.RESPOND_NOT_FOUND):
                raise NextcloudExceptionNotFound(reason=ocs_meta["message"], info=info)
            if ocs_meta["statuscode"] == 304:
                raise NextcloudExceptionNotModified(reason=ocs_meta["message"], info=info)
            raise NextcloudException(status_code=ocs_meta["statuscode"], reason=ocs_meta["message"], info=info)
        return response_data["ocs"]["data"]

    async def update_server_info(self) -> None:
        self._capabilities = await self.ocs("GET", "/ocs/v1.php/cloud/capabilities")

    @property
    async def capabilities(self) -> dict:
        if not self._capabilities:
            await self.update_server_info()
        return self._capabilities["capabilities"]

    @property
    async def nc_version(self) -> ServerVersion:
        if not self._capabilities:
            await self.update_server_info()
        v = self._capabilities["version"]
        return ServerVersion(
            major=v["major"],
            minor=v["minor"],
            micro=v["micro"],
            string=v["string"],
            extended_support=v["extendedSupport"],
        )

    @property
    async def user(self) -> str:
        """Current user ID. Can be different from the login name."""
        if isinstance(self, AsyncNcSession) and not self._user:  # do not trigger for NextcloudApp
            self._user = (await self.ocs("GET", "/ocs/v1.php/cloud/user"))["id"]
        return self._user

    def set_user(self, user: str) -> None:
        self._user = user

    async def download2stream(self, url_path: str, fp, dav: bool = False, **kwargs):
        if isinstance(fp, str | pathlib.Path):
            with builtins.open(fp, "wb") as f:
                await self.download2fp(url_path, f, dav, **kwargs)
        elif hasattr(fp, "write"):
            await self.download2fp(url_path, fp, dav, **kwargs)
        else:
            raise TypeError("`fp` must be a path to file or an object with `write` method.")

    def _get_adapter_kwargs(self, dav: bool) -> dict[str, typing.Any]:
        if dav:
            return {
                "base_url": self.cfg.dav_endpoint,
                "timeout": self.cfg.options.timeout_dav,
                "event_hooks": {"request": [], "response": [self._response_event]},
            }
        return {
            "base_url": self.cfg.endpoint,
            "timeout": self.cfg.options.timeout,
            "event_hooks": {"request": [self._request_event_ocs], "response": [self._response_event]},
        }

    async def _request_event_ocs(self, request: Request) -> None:
        str_url = str(request.url)
        if re.search(self._ocs_regexp, str_url) is not None:  # this is OCS call
            request.url = request.url.copy_merge_params({"format": "json"})
            request.headers["Accept"] = "application/json"

    async def _response_event(self, response: Response) -> None:
        str_url = str(response.request.url)
        # we do not want ResponseHeaders for those two endpoints, as call to them can occur during DAV calls.
        for i in ("/ocs/v1.php/cloud/capabilities?format=json", "/ocs/v1.php/cloud/user?format=json"):
            if str_url.endswith(i):
                return
        self.response_headers = response.headers

    async def download2fp(self, url_path: str, fp, dav: bool, params=None, **kwargs):
        adapter = self.adapter_dav if dav else self.adapter
        async with adapter.stream("GET", url_path, params=params) as response:
            check_error(response)
            async for data_chunk in response.aiter_raw(chunk_size=kwargs.get("chunk_size", 5 * 1024 * 1024)):
                fp.write(data_chunk)


class NcSession(NcSessionBasic):
    cfg: Config

    def __init__(self, **kwargs):
        self.cfg = Config(**kwargs)
        super().__init__()

    def _create_adapter(self, dav: bool = False) -> AsyncClient | Client:
        return Client(
            follow_redirects=True,
            limits=self.limits,
            verify=self.cfg.options.nc_cert,
            **self._get_adapter_kwargs(dav),
            auth=self.cfg.auth,
        )


class AsyncNcSession(AsyncNcSessionBasic):
    cfg: Config

    def __init__(self, **kwargs):
        self.cfg = Config(**kwargs)
        super().__init__()

    def _create_adapter(self, dav: bool = False) -> AsyncClient | Client:
        return AsyncClient(
            follow_redirects=True,
            limits=self.limits,
            verify=self.cfg.options.nc_cert,
            **self._get_adapter_kwargs(dav),
            auth=self.cfg.auth,
        )


class NcSessionAppBasic(ABC):
    cfg: AppConfig
    _user: str
    adapter: AsyncClient | Client
    adapter_dav: AsyncClient | Client

    def __init__(self, **kwargs):
        self.cfg = AppConfig(**kwargs)
        super().__init__(**kwargs)

    def sign_check(self, request: HTTPConnection) -> str:
        headers = {
            "AA-VERSION": request.headers.get("AA-VERSION", ""),
            "EX-APP-ID": request.headers.get("EX-APP-ID", ""),
            "EX-APP-VERSION": request.headers.get("EX-APP-VERSION", ""),
            "AUTHORIZATION-APP-API": request.headers.get("AUTHORIZATION-APP-API", ""),
        }

        empty_headers = [k for k, v in headers.items() if not v]
        if empty_headers:
            raise ValueError(f"Missing required headers:{empty_headers}")

        if headers["EX-APP-ID"] != self.cfg.app_name:
            raise ValueError(f"Invalid EX-APP-ID:{headers['EX-APP-ID']} != {self.cfg.app_name}")

        username, app_secret = get_username_secret_from_headers(headers)
        if app_secret != self.cfg.app_secret:
            raise ValueError(f"Invalid App secret:{app_secret} != {self.cfg.app_secret}")
        return username


class NcSessionApp(NcSessionAppBasic, NcSessionBasic):
    cfg: AppConfig

    def _create_adapter(self, dav: bool = False) -> AsyncClient | Client:
        r = self._get_adapter_kwargs(dav)
        r["event_hooks"]["request"].append(self._add_auth)
        return Client(
            follow_redirects=True,
            limits=self.limits,
            verify=self.cfg.options.nc_cert,
            **r,
            headers={
                "AA-VERSION": self.cfg.aa_version,
                "EX-APP-ID": self.cfg.app_name,
                "EX-APP-VERSION": self.cfg.app_version,
            },
        )

    def _add_auth(self, request: Request):
        request.headers.update(
            {"AUTHORIZATION-APP-API": b64encode(f"{self._user}:{self.cfg.app_secret}".encode("UTF=8"))}
        )


class AsyncNcSessionApp(NcSessionAppBasic, AsyncNcSessionBasic):
    cfg: AppConfig

    def _create_adapter(self, dav: bool = False) -> AsyncClient | Client:
        r = self._get_adapter_kwargs(dav)
        r["event_hooks"]["request"].append(self._add_auth)
        return AsyncClient(
            follow_redirects=True,
            limits=self.limits,
            verify=self.cfg.options.nc_cert,
            **r,
            headers={
                "AA-VERSION": self.cfg.aa_version,
                "EX-APP-ID": self.cfg.app_name,
                "EX-APP-VERSION": self.cfg.app_version,
            },
        )

    async def _add_auth(self, request: Request):
        request.headers.update(
            {"AUTHORIZATION-APP-API": b64encode(f"{self._user}:{self.cfg.app_secret}".encode("UTF=8"))}
        )
