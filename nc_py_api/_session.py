"""Session represents one connection to Nextcloud. All related stuff for these live here."""

import asyncio
import hmac
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from hashlib import sha256
from json import dumps, loads
from os import environ
from typing import Optional, TypedDict, Union
from urllib.parse import quote, urlencode

from fastapi import Request
from httpx import Client
from httpx import Headers as HttpxHeaders
from httpx import Limits, ReadTimeout, Response

try:
    from xxhash import xxh64
except ImportError as ex:
    from ._deffered_error import DeferredError

    xxh64 = DeferredError(ex)


from . import options
from ._exceptions import NextcloudException, NextcloudExceptionNotFound, check_error


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

    def __init__(self, **kwargs):
        self.xdebug_session = kwargs.get("xdebug_session", options.XDEBUG_SESSION)
        self.timeout = kwargs.get("npa_timeout", options.NPA_TIMEOUT)
        self.timeout_dav = kwargs.get("npa_timeout_dav", options.NPA_TIMEOUT_DAV)
        self._nc_cert = kwargs.get("npa_nc_cert", options.NPA_NC_CERT)

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

    ae_version: str
    """AppEcosystem version"""
    app_name: str
    """Application ID"""
    app_version: str
    """Application version"""
    app_secret: bytes
    """Application authentication secret"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ae_version = self._get_config_value("ae_version", raise_not_found=False, **kwargs)
        if not self.ae_version:
            self.ae_version = "1.0.0"
        self.app_name = self._get_config_value("app_id", **kwargs)
        self.app_version = self._get_config_value("app_version", **kwargs)
        self.app_secret = self._get_config_value("app_secret", **kwargs).encode("UTF-8")


class NcSessionBasic(ABC):
    adapter: Client
    cfg: BasicConfig
    user: str
    custom_headers: dict
    _capabilities: dict
    response_headers: HttpxHeaders

    @abstractmethod
    def __init__(self, **kwargs):
        self._capabilities = {}
        self.user = kwargs.get("user", "")
        self.custom_headers = kwargs.get("headers", {})
        self.limits = Limits(max_keepalive_connections=20, max_connections=20, keepalive_expiry=60.0)
        self.init_adapter()
        self.response_headers = HttpxHeaders()

    def __del__(self):
        if hasattr(self, "adapter") and self.adapter:
            self.adapter.close()

    def get_stream(self, path: str, params: Optional[dict] = None, **kwargs) -> Iterator[Response]:
        return self._get_stream(
            f"{quote(path)}?{urlencode(params, True)}" if params else quote(path), kwargs.get("headers", {}), **kwargs
        )

    def _get_stream(self, path_params: str, headers: dict, **kwargs) -> Iterator[Response]:
        self.init_adapter()
        timeout = kwargs.pop("timeout", self.cfg.options.timeout)
        return self.adapter.stream(
            "GET", f"{self.cfg.endpoint}{path_params}", headers=headers, timeout=timeout, **kwargs
        )

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
        data_bytes = None
        if data is not None:
            data_bytes = data.encode("UTF-8") if isinstance(data, str) else data
        elif json is not None:
            headers.update({"Content-Type": "application/json"})
            data_bytes = dumps(json).encode("utf-8")
        return self._ocs(method, f"{quote(path)}?{urlencode(params, True)}", headers, data=data_bytes, **kwargs)

    def _ocs(self, method: str, path_params: str, headers: dict, data: Optional[bytes], **kwargs):
        self.init_adapter()
        url_params = f"{self.cfg.endpoint}{path_params}"
        info = f"request: method={method}, url={url_params}"
        nested_req = kwargs.pop("nested_req", False)
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
            raise NextcloudException(status_code=ocs_meta["statuscode"], reason=ocs_meta["message"], info=info)
        return response_data["ocs"]["data"]

    def dav(self, method: str, path: str, data: Optional[Union[str, bytes]] = None, **kwargs) -> Response:
        headers = kwargs.pop("headers", {})
        data_bytes = None
        if data is not None:
            data_bytes = data.encode("UTF-8") if isinstance(data, str) else data
        return self._dav(method, quote(self.cfg.dav_url_suffix + path), headers, data_bytes, **kwargs)

    def dav_stream(
        self, method: str, path: str, data: Optional[Union[str, bytes]] = None, **kwargs
    ) -> Iterator[Response]:
        headers = kwargs.pop("headers", {})
        data_bytes = None
        if data is not None:
            data_bytes = data.encode("UTF-8") if isinstance(data, str) else data
        return self._dav_stream(method, quote(self.cfg.dav_url_suffix + path), headers, data_bytes, **kwargs)

    def _dav(self, method: str, path: str, headers: dict, data: Optional[bytes], **kwargs) -> Response:
        self.init_adapter()
        timeout = kwargs.pop("timeout", self.cfg.options.timeout_dav)
        result = self.adapter.request(
            method, self.cfg.endpoint + path, headers=headers, content=data, timeout=timeout, **kwargs
        )
        self.response_headers = result.headers
        return result

    def _dav_stream(self, method: str, path: str, headers: dict, data: Optional[bytes], **kwargs) -> Iterator[Response]:
        self.init_adapter()
        timeout = kwargs.pop("timeout", self.cfg.options.timeout_dav)
        return self.adapter.stream(
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

    @abstractmethod
    def _create_adapter(self) -> Client:
        pass  # pragma: no cover

    def update_server_info(self) -> None:
        self._capabilities = self.ocs(method="GET", path="/ocs/v1.php/cloud/capabilities")

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
        return "/ocs/v1.php/apps/app_ecosystem_v2/api/v1"


class NcSession(NcSessionBasic):
    cfg: Config

    def __init__(self, **kwargs):
        self.cfg = Config(**kwargs)
        super().__init__(user=self.cfg.auth[0])

    def _create_adapter(self) -> Client:
        return Client(auth=self.cfg.auth, follow_redirects=True, limits=self.limits, verify=self.cfg.options.nc_cert)


class NcSessionApp(NcSessionBasic):
    cfg: AppConfig

    def __init__(self, **kwargs):
        self.cfg = AppConfig(**kwargs)
        super().__init__(**kwargs)

    def _get_stream(self, path_params: str, headers: dict, **kwargs) -> Iterator[Response]:
        self.sign_request("GET", path_params, headers, None)
        return super()._get_stream(path_params, headers, **kwargs)

    def _ocs(self, method: str, path_params: str, headers: dict, data: Optional[bytes], **kwargs):
        self.sign_request(method, path_params, headers, data)
        return super()._ocs(method, path_params, headers, data, **kwargs)

    def _dav(self, method: str, path: str, headers: dict, data: Optional[bytes], **kwargs) -> Response:
        self.sign_request(method, path, headers, data)
        return super()._dav(method, path, headers, data, **kwargs)

    def _dav_stream(self, method: str, path: str, headers: dict, data: Optional[bytes], **kwargs) -> Iterator[Response]:
        self.sign_request(method, path, headers, data)
        return super()._dav_stream(method, path, headers, data, **kwargs)

    def _create_adapter(self) -> Client:
        adapter = Client(follow_redirects=True, limits=self.limits, verify=self.cfg.options.nc_cert)
        adapter.headers.update(
            {
                "AE-VERSION": self.cfg.ae_version,
                "EX-APP-ID": self.cfg.app_name,
                "EX-APP-VERSION": self.cfg.app_version,
            }
        )
        return adapter

    def sign_request(self, method: str, url_params: str, headers: dict, data: Optional[bytes]) -> None:
        data_hash = xxh64()
        if data and method != "GET":
            data_hash.update(data)

        sign_headers = {
            "AE-VERSION": self.adapter.headers.get("AE-VERSION"),
            "EX-APP-ID": self.adapter.headers.get("EX-APP-ID"),
            "EX-APP-VERSION": self.adapter.headers.get("EX-APP-VERSION"),
            "NC-USER-ID": self.user,
            "AE-DATA-HASH": data_hash.hexdigest(),
            "AE-SIGN-TIME": str(int(datetime.now(timezone.utc).timestamp())),
        }
        if not sign_headers["NC-USER-ID"]:
            sign_headers.pop("NC-USER-ID")

        request_to_sign = (
            method.encode("UTF-8")
            + url_params.encode("UTF-8")
            + dumps(sign_headers, separators=(",", ":")).encode("UTF-8")
        )
        hmac_sign = hmac.new(self.cfg.app_secret, request_to_sign, digestmod=sha256)
        headers.update(
            {
                "AE-SIGNATURE": hmac_sign.hexdigest(),
                "AE-DATA-HASH": sign_headers["AE-DATA-HASH"],
                "AE-SIGN-TIME": sign_headers["AE-SIGN-TIME"],
            }
        )
        if "NC-USER-ID" in sign_headers:
            headers["NC-USER-ID"] = sign_headers["NC-USER-ID"]

    def sign_check(self, request: Request) -> None:
        current_time = int(datetime.now(timezone.utc).timestamp())
        headers = {
            "AE-VERSION": request.headers.get("AE-VERSION", ""),
            "EX-APP-ID": request.headers.get("EX-APP-ID", ""),
            "EX-APP-VERSION": request.headers.get("EX-APP-VERSION", ""),
            "NC-USER-ID": request.headers.get("NC-USER-ID", ""),
            "AE-DATA-HASH": request.headers.get("AE-DATA-HASH", ""),
            "AE-SIGN-TIME": request.headers.get("AE-SIGN-TIME", ""),
        }
        if not headers["NC-USER-ID"]:
            headers.pop("NC-USER-ID")

        empty_headers = [k for k, v in headers.items() if not v]
        if empty_headers:
            raise ValueError(f"Missing required headers:{empty_headers}")

        our_version = self.adapter.headers.get("EX-APP-VERSION", "")
        if headers["EX-APP-VERSION"] != our_version:
            raise ValueError(f"Invalid EX-APP-VERSION:{headers['EX-APP-VERSION']} <=> {our_version}")

        request_time = int(headers["AE-SIGN-TIME"])
        if request_time < current_time - 5 * 60 or request_time > current_time + 5 * 60:
            raise ValueError(f"Invalid AE-SIGN-TIME:{request_time} <=> {current_time}")

        query_params = f"?{request.url.components.query}" if request.url.components.query else ""
        request_to_sign = (
            request.method.upper() + request.url.components.path + query_params + dumps(headers, separators=(",", ":"))
        )
        hmac_sign = hmac.new(self.cfg.app_secret, request_to_sign.encode("UTF-8"), digestmod=sha256).hexdigest()
        request_ae_sign = request.headers.get("AE-SIGNATURE", "")
        if hmac_sign != request_ae_sign:
            raise ValueError(f"Invalid AE-SIGNATURE:{hmac_sign} != {request_ae_sign}")

        data_hash = xxh64()
        data = asyncio.run(request.body())
        if data:
            data_hash.update(data)
        ae_data_hash = data_hash.hexdigest()
        if ae_data_hash != headers["AE-DATA-HASH"]:
            raise ValueError(f"Invalid AE-DATA-HASH:{ae_data_hash} !={headers['AE-DATA-HASH']}")
        if headers["EX-APP-ID"] != self.cfg.app_name:
            raise ValueError(f"Invalid EX-APP-ID:{headers['EX-APP-ID']} != {self.cfg.app_name}")
