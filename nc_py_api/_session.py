"""Session represents one connection to Nextcloud. All related stuff for these live here."""

import typing
from abc import ABC, abstractmethod
from base64 import b64encode
from dataclasses import dataclass
from enum import IntEnum
from json import dumps, loads
from os import environ
from typing import Optional, TypedDict, Union
from urllib.parse import quote, urlencode

from fastapi import Request as FastAPIRequest
from httpx import Client, Headers, Limits, ReadTimeout, Request, Response

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


class ServerVersion(TypedDict):
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
    timeout: Optional[int]
    timeout_dav: Optional[int]
    _nc_cert: Union[str, bool]
    upload_chunk_v2: bool

    def __init__(self, **kwargs):
        self.xdebug_session = kwargs.get("xdebug_session", options.XDEBUG_SESSION)
        self.timeout = kwargs.get("npa_timeout", options.NPA_TIMEOUT)
        self.timeout_dav = kwargs.get("npa_timeout_dav", options.NPA_TIMEOUT_DAV)
        self._nc_cert = kwargs.get("npa_nc_cert", options.NPA_NC_CERT)
        self.upload_chunk_v2 = kwargs.get("chunked_upload_v2", options.CHUNKED_UPLOAD_V2)

    @property
    def nc_cert(self) -> Union[str, bool]:
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
        self.auth = (self._get_config_value("nc_auth_user", **kwargs), self._get_config_value("nc_auth_pass", **kwargs))


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
            self.aa_version = "1.0.0"
        self.app_name = self._get_config_value("app_id", **kwargs)
        self.app_version = self._get_config_value("app_version", **kwargs)
        self.app_secret = self._get_config_value("app_secret", **kwargs)


class NcSessionBasic(ABC):
    adapter: Client
    adapter_dav: Client
    cfg: BasicConfig
    custom_headers: dict
    response_headers: Headers
    response_headers_dav: Headers
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
        self.response_headers_dav = Headers()

    def __del__(self):
        if hasattr(self, "adapter") and self.adapter:
            self.adapter.close()
        if hasattr(self, "adapter_dav") and self.adapter_dav:
            self.adapter_dav.close()

    def ocs(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        data: Optional[Union[bytes, str]] = None,
        json: Optional[Union[dict, list]] = None,
        **kwargs,
    ):
        method = method.upper()
        if params is None:
            params = {}
        params.update({"format": "json"})
        headers = kwargs.pop("headers", {})
        data_bytes = self.__data_to_bytes(headers, data, json)
        return self._ocs(method, f"{quote(path)}?{urlencode(params, True)}", headers, data=data_bytes, **kwargs)

    def _ocs(self, method: str, path_params: str, headers: dict, data: Optional[bytes], **kwargs):
        self.init_adapter()
        info = f"request: method={method}, path_params={path_params}"
        nested_req = kwargs.pop("nested_req", False)
        not_parse = kwargs.pop("not_parse", False)
        try:
            timeout = kwargs.pop("timeout", self.cfg.options.timeout)
            response = self.adapter.request(
                method, path_params, headers=headers, content=data, timeout=timeout, **kwargs
            )
        except ReadTimeout:
            raise NextcloudException(408, info=info) from None

        check_error(response.status_code, info)
        if not_parse:
            return response
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
                return self._ocs(method, path_params, headers, data, **kwargs, nested_req=True)
            if ocs_meta["statuscode"] in (404, OCSRespond.RESPOND_NOT_FOUND):
                raise NextcloudExceptionNotFound(reason=ocs_meta["message"], info=info)
            if ocs_meta["statuscode"] == 304:
                raise NextcloudExceptionNotModified(reason=ocs_meta["message"], info=info)
            raise NextcloudException(status_code=ocs_meta["statuscode"], reason=ocs_meta["message"], info=info)
        return response_data["ocs"]["data"]

    def init_adapter(self, restart=False) -> None:
        if getattr(self, "adapter", None) is None or restart:
            if restart and hasattr(self, "adapter"):
                self.adapter.close()
            self.adapter = self._create_adapter()
            self.adapter.headers.update({"OCS-APIRequest": "true"})
            if self.custom_headers:
                self.adapter.headers.update(self.custom_headers)
            if options.XDEBUG_SESSION:
                self.adapter.cookies.set("XDEBUG_SESSION", options.XDEBUG_SESSION)
            self._capabilities = {}

    def init_adapter_dav(self, restart=False) -> None:
        if getattr(self, "adapter_dav", None) is None or restart:
            if restart and hasattr(self, "adapter"):
                self.adapter.close()
            self.adapter_dav = self._create_adapter(dav=True)
            if self.custom_headers:
                self.adapter_dav.headers.update(self.custom_headers)
            if options.XDEBUG_SESSION:
                self.adapter_dav.cookies.set("XDEBUG_SESSION", options.XDEBUG_SESSION)

    @abstractmethod
    def _create_adapter(self, dav: bool = False) -> Client:
        pass  # pragma: no cover

    def update_server_info(self) -> None:
        self._capabilities = self.ocs(method="GET", path="/ocs/v1.php/cloud/capabilities")

    @property
    def user(self) -> str:
        """Current user ID. Can be different from the login name."""
        if isinstance(self, NcSession) and not self._user:  # do not trigger for NextcloudApp
            self._user = self.ocs(method="GET", path="/ocs/v1.php/cloud/user")["id"]
        return self._user

    @user.setter
    def user(self, value: str):
        self._user = value

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
    def ae_url(self) -> str:
        """Return base url for the App Ecosystem endpoints."""
        return "/ocs/v1.php/apps/app_api/api/v1"

    @staticmethod
    def __data_to_bytes(
        headers: dict, data: Optional[Union[bytes, str]] = None, json: Optional[Union[dict, list]] = None
    ) -> typing.Optional[bytes]:
        if data is not None:
            return data.encode("UTF-8") if isinstance(data, str) else data
        if json is not None:
            headers.update({"Content-Type": "application/json"})
            return dumps(json).encode("utf-8")
        return None

    def _get_adapter_kwargs(self, dav: bool) -> dict[str, typing.Any]:
        if dav:
            return {
                "base_url": self.cfg.dav_endpoint,
                "timeout": self.cfg.options.timeout_dav,
                "event_hooks": {"response": [self._response_event_dav]},
            }
        return {
            "base_url": self.cfg.endpoint,
            "timeout": self.cfg.options.timeout,
            "event_hooks": {"response": [self._response_event]},
        }

    def _response_event(self, response: Response):
        str_url = str(response.request.url)
        # we do not want ResponseHeaders for those two endpoints, as call to them can occur during DAV calls.
        for i in ("/ocs/v1.php/cloud/capabilities?format=json", "/ocs/v1.php/cloud/user?format=json"):
            if str_url.endswith(i):
                return
        self.response_headers = response.headers

    def _response_event_dav(self, response: Response):
        self.response_headers_dav = response.headers


class NcSession(NcSessionBasic):
    cfg: Config

    def __init__(self, **kwargs):
        self.cfg = Config(**kwargs)
        super().__init__()

    def _create_adapter(self, dav: bool = False) -> Client:
        return Client(
            follow_redirects=True,
            limits=self.limits,
            verify=self.cfg.options.nc_cert,
            **self._get_adapter_kwargs(dav),
            auth=self.cfg.auth,
        )


class NcSessionApp(NcSessionBasic):
    cfg: AppConfig

    def __init__(self, **kwargs):
        self.cfg = AppConfig(**kwargs)
        super().__init__(**kwargs)

    def _create_adapter(self, dav: bool = False) -> Client:
        r = self._get_adapter_kwargs(dav)
        r["event_hooks"]["request"] = [self._add_auth]
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
        request.headers.update({
            "AUTHORIZATION-APP-API": b64encode(f"{self._user}:{self.cfg.app_secret}".encode("UTF=8"))
        })

    def sign_check(self, request: FastAPIRequest) -> None:
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

        our_version = self.adapter.headers.get("EX-APP-VERSION", "")
        if headers["EX-APP-VERSION"] != our_version:
            raise ValueError(f"Invalid EX-APP-VERSION:{headers['EX-APP-VERSION']} <=> {our_version}")

        app_secret = get_username_secret_from_headers(headers)[1]
        if app_secret != self.cfg.app_secret:
            raise ValueError(f"Invalid App secret:{app_secret} != {self.cfg.app_secret}")
