"""Session represents one connection to Nextcloud. All related stuff for these live here."""
import typing
from abc import ABC, abstractmethod
from base64 import b64encode
from collections.abc import Iterator
from dataclasses import dataclass
from enum import IntEnum
from json import dumps, loads
from os import environ
from typing import Optional, TypedDict, Union
from urllib.parse import quote, urlencode

from fastapi import Request
from httpx import Client
from httpx import Headers as HttpxHeaders
from httpx import Limits, ReadTimeout, Response

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
    response_headers: HttpxHeaders
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
        self.response_headers = HttpxHeaders()

    def __del__(self):
        if hasattr(self, "adapter") and self.adapter:
            self.adapter.close()
        if hasattr(self, "adapter_dav") and self.adapter_dav:
            self.adapter_dav.close()

    def get_stream(self, path: str, params: Optional[dict] = None, **kwargs) -> Iterator[Response]:
        headers = kwargs.pop("headers", {})
        return self._get_stream(
            f"{quote(path)}?{urlencode(params, True)}" if params else quote(path), headers=headers, **kwargs
        )

    def _get_stream(self, path_params: str, headers: dict, **kwargs) -> Iterator[Response]:
        self.init_adapter()
        timeout = kwargs.pop("timeout", self.cfg.options.timeout)
        return self.adapter.stream(
            "GET", f"{self.cfg.endpoint}{path_params}", headers=headers, timeout=timeout, **kwargs
        )

    def request(
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
        return self._ocs(method, f"{quote(path)}?{urlencode(params, True)}", headers, data_bytes, not_parse=True)

    def request_json(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        data: Optional[Union[bytes, str]] = None,
        json: Optional[Union[dict, list]] = None,
        **kwargs,
    ) -> dict:
        r = self.request(method, path, params, data, json, **kwargs)
        return loads(r.text) if r.status_code != 304 else {}

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
        url_params = f"{self.cfg.endpoint}{path_params}"
        info = f"request: method={method}, url={url_params}"
        nested_req = kwargs.pop("nested_req", False)
        not_parse = kwargs.pop("not_parse", False)
        try:
            timeout = kwargs.pop("timeout", self.cfg.options.timeout)
            if method == "GET":
                response = self.adapter.get(url_params, headers=headers, timeout=timeout, **kwargs)
            else:
                response = self.adapter.request(
                    method, url_params, headers=headers, content=data, timeout=timeout, **kwargs
                )
        except ReadTimeout:
            raise NextcloudException(408, info=info) from None

        self.response_headers = response.headers
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

    def dav(
        self,
        method: str,
        path: str,
        data: Optional[Union[str, bytes]] = None,
        json: Optional[Union[dict, list]] = None,
        **kwargs,
    ) -> Response:
        headers = kwargs.pop("headers", {})
        data_bytes = self.__data_to_bytes(headers, data, json)
        return self._dav(
            method,
            quote(self.cfg.dav_url_suffix + path) if isinstance(path, str) else path,
            headers,
            data_bytes,
            **kwargs,
        )

    def dav_stream(
        self, method: str, path: str, data: Optional[Union[str, bytes]] = None, **kwargs
    ) -> Iterator[Response]:
        headers = kwargs.pop("headers", {})
        data_bytes = None
        if data is not None:
            data_bytes = data.encode("UTF-8") if isinstance(data, str) else data
        return self._dav_stream(method, quote(self.cfg.dav_url_suffix + path), headers, data_bytes, **kwargs)

    def _dav(self, method: str, path: str, headers: dict, data: Optional[bytes], **kwargs) -> Response:
        self.init_adapter_dav()
        timeout = kwargs.pop("timeout", self.cfg.options.timeout_dav)
        result = self.adapter_dav.request(
            method,
            self.cfg.endpoint + path if isinstance(path, str) else str(path),
            headers=headers,
            content=data,
            timeout=timeout,
            **kwargs,
        )
        self.response_headers = result.headers
        return result

    def _dav_stream(self, method: str, path: str, headers: dict, data: Optional[bytes], **kwargs) -> Iterator[Response]:
        self.init_adapter_dav()
        timeout = kwargs.pop("timeout", self.cfg.options.timeout_dav)
        return self.adapter_dav.stream(
            method, self.cfg.endpoint + path, headers=headers, content=data, timeout=timeout, **kwargs
        )

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
            self.adapter_dav = self._create_adapter()
            if self.custom_headers:
                self.adapter_dav.headers.update(self.custom_headers)
            if options.XDEBUG_SESSION:
                self.adapter_dav.cookies.set("XDEBUG_SESSION", options.XDEBUG_SESSION)

    @abstractmethod
    def _create_adapter(self) -> Client:
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


class NcSession(NcSessionBasic):
    cfg: Config

    def __init__(self, **kwargs):
        self.cfg = Config(**kwargs)
        super().__init__()

    def _create_adapter(self) -> Client:
        return Client(auth=self.cfg.auth, follow_redirects=True, limits=self.limits, verify=self.cfg.options.nc_cert)


class NcSessionApp(NcSessionBasic):
    cfg: AppConfig

    def __init__(self, **kwargs):
        self.cfg = AppConfig(**kwargs)
        super().__init__(**kwargs)

    def _get_stream(self, path_params: str, headers: dict, **kwargs) -> Iterator[Response]:
        self.sign_request(headers)
        return super()._get_stream(path_params, headers, **kwargs)

    def _ocs(self, method: str, path_params: str, headers: dict, data: Optional[bytes], **kwargs):
        self.sign_request(headers)
        return super()._ocs(method, path_params, headers, data, **kwargs)

    def _dav(self, method: str, path: str, headers: dict, data: Optional[bytes], **kwargs) -> Response:
        self.sign_request(headers)
        return super()._dav(method, path, headers, data, **kwargs)

    def _dav_stream(self, method: str, path: str, headers: dict, data: Optional[bytes], **kwargs) -> Iterator[Response]:
        self.sign_request(headers)
        return super()._dav_stream(method, path, headers, data, **kwargs)

    def _create_adapter(self) -> Client:
        adapter = Client(follow_redirects=True, limits=self.limits, verify=self.cfg.options.nc_cert)
        adapter.headers.update(
            {
                "AA-VERSION": self.cfg.aa_version,
                "EX-APP-ID": self.cfg.app_name,
                "EX-APP-VERSION": self.cfg.app_version,
            }
        )
        return adapter

    def sign_request(self, headers: dict) -> None:
        headers["AUTHORIZATION-APP-API"] = b64encode(f"{self._user}:{self.cfg.app_secret}".encode("UTF=8"))

    def sign_check(self, request: Request) -> None:
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
