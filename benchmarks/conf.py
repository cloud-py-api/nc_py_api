from typing import Optional

from nc_py_api import Nextcloud, NextcloudApp

NC_CFGS = {
    "http://stable27.local/index.php": {
        # NC_APP
        "secret": (
            "tC6vkwPhcppjMykD1r0n9NlI95uJMBYjs5blpIcA1PAdoPDmc5qoAjaBAkyocZ6E"
            "X1T8Pi+T5papEolTLxz3fJSPS8ffC4204YmggxPsbJdCkXHWNPHKWS9B+vTj2SIV"
        ),
        "app_id": "nc_py_api",
        "app_version": "1.0.0",
        "user": "admin",
        # NC
        "nc_auth_user": "admin",
        "nc_auth_pass": "admin",
    },
    "http://nextcloud.local/index.php": {
        # NC_APP
        "secret": (
            "tC6vkwPhcppjMykD1r0n9NlI95uJMBYjs5blpIcA1PAdoPDmc5qoAjaBAkyocZ6E"
            "X1T8Pi+T5papEolTLxz3fJSPS8ffC4204YmggxPsbJdCkXHWNPHKWS9B+vTj2SIV"
        ),
        "app_id": "nc_py_api",
        "app_version": "1.0.0",
        "user": "admin",
        # NC
        "nc_auth_user": "admin",
        "nc_auth_pass": "admin",
    },
}


def init_nc(url, cfg) -> Optional[Nextcloud]:
    if "nc_auth_user" in cfg and "nc_auth_pass" in cfg:
        return Nextcloud(nc_auth_user=cfg["nc_auth_user"], nc_auth_pass=cfg["nc_auth_pass"], nextcloud_url=url)
    return None


def init_nc_app(url, cfg) -> Optional[NextcloudApp]:
    if "secret" in cfg and "app_id" in cfg:
        return NextcloudApp(
            app_id=cfg["app_id"],
            app_version=cfg["app_version"],
            app_secret=cfg["secret"],
            nextcloud_url=url,
            user=cfg["user"],
        )
    return None
