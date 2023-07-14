from os import environ

from nc_py_api import NextcloudApp, Nextcloud


if not environ.get("CI", False):  # For local tests
    environ["NC_AUTH_USER"] = "admin"
    environ["NC_AUTH_PASS"] = "admin"  # "MrtGY-KfY24-iiDyg-cr4n4-GLsNZ"
    environ["NEXTCLOUD_URL"] = "http://nextcloud.local"
    environ["APP_ID"] = "nc_py_api"
    environ["APP_VERSION"] = "1.0.0"
    environ["APP_SECRET"] = "12345"

if environ.get("SKIP_NC_WO_AE", False):
    NC = None
else:
    NC = Nextcloud()

NC_APP = NextcloudApp(user="admin")
if "app_ecosystem_v2" not in NC_APP.capabilities:
    NC_APP = None

NC_TO_TEST = []
if NC:
    NC_TO_TEST.append(NC)
if NC_APP:
    NC_TO_TEST.append(NC_APP)

NC_VERSION = NC_TO_TEST[0].srv_version if NC_TO_TEST else {}
