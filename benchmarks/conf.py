from nc_py_api import Nextcloud, NextcloudApp

NC_CFGS = {
    "http://stable26.local": {
        # NC_APP
        "secret": "12345",
        "app_id": "nc_py_api",
        "app_version": "1.0.0",
        "user": "admin",
        # NC
        "nc_auth_user": "admin",
        "nc_auth_pass": "admin",
        "nc_auth_app_pass": "kFEfH-cqR8T-563tB-8CAjd-96LNj",
    },
    "http://stable27.local": {
        # NC_APP
        "secret": "12345",
        "app_id": "nc_py_api",
        "app_version": "1.0.0",
        "user": "admin",
        # NC
        "nc_auth_user": "admin",
        "nc_auth_pass": "admin",
        "nc_auth_app_pass": "Npi8A-LAtWM-WaPm8-CPpEA-jq9od",
    },
    "http://nextcloud.local": {
        # NC_APP
        "secret": "12345",
        "app_id": "nc_py_api",
        "app_version": "1.0.0",
        "user": "admin",
        # NC
        "nc_auth_user": "admin",
        "nc_auth_pass": "admin",
        "nc_auth_app_pass": "yEaoa-5Z96a-Z7SHs-44spP-EkC4o",
    },
}


def init_nc(url, cfg) -> Nextcloud | None:
    if cfg.get("nc_auth_user", "") and cfg.get("nc_auth_pass", ""):
        return Nextcloud(nc_auth_user=cfg["nc_auth_user"], nc_auth_pass=cfg["nc_auth_pass"], nextcloud_url=url)
    return None


def init_nc_by_app_pass(url, cfg) -> Nextcloud | None:
    if cfg.get("nc_auth_user", "") and cfg.get("nc_auth_app_pass", ""):
        return Nextcloud(nc_auth_user=cfg["nc_auth_user"], nc_auth_pass=cfg["nc_auth_app_pass"], nextcloud_url=url)
    return None


def init_nc_app(url, cfg) -> NextcloudApp | None:
    if cfg.get("secret", "") and cfg.get("app_id", ""):
        return NextcloudApp(
            app_id=cfg["app_id"],
            app_version=cfg["app_version"],
            app_secret=cfg["secret"],
            nextcloud_url=url,
            user=cfg["user"],
        )
    return None
