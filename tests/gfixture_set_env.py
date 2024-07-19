from os import environ

if not environ.get("CI", False):  # For local tests
    environ["NC_AUTH_USER"] = "admin"
    environ["NC_AUTH_PASS"] = "admin"  # "MrtGY-KfY24-iiDyg-cr4n4-GLsNZ"
    environ["NEXTCLOUD_URL"] = environ.get("NEXTCLOUD_URL", "http://stable29.local")
    # environ["NEXTCLOUD_URL"] = environ.get("NEXTCLOUD_URL", "http://stable30.local")
    # environ["NEXTCLOUD_URL"] = environ.get("NEXTCLOUD_URL", "http://nextcloud.local")
    environ["APP_ID"] = "nc_py_api"
    environ["APP_VERSION"] = "1.0.0"
    environ["APP_SECRET"] = "12345"
    environ["APP_PORT"] = "9009"
