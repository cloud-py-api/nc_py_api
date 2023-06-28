from os import environ

from nc_py_api import NextcloudApp, Nextcloud


secret = "tC6vkwPhcppjMykD1r0n9NlI95uJMBYjs5blpIcA1PAdoPDmc5qoAjaBAkyocZ6E" \
            "X1T8Pi+T5papEolTLxz3fJSPS8ffC4204YmggxPsbJdCkXHWNPHKWS9B+vTj2SIV"
if not environ.get("CI", False):  # For local tests
    environ["nc_auth_user"] = "admin"
    environ["nc_auth_pass"] = "admin"  # "MrtGY-KfY24-iiDyg-cr4n4-GLsNZ"
    environ["nextcloud_url"] = "http://nextcloud.local/index.php"
    environ["app_name"] = "nc_py_api"
    environ["app_version"] = "1.0.0"
    environ["app_secret"] = secret

NC = Nextcloud()
if environ.get("SKIP_NC_WO_AE", False):
    NC = None

NC_APP = NextcloudApp(user="admin")
if "app_ecosystem_v2" not in NC_APP.capabilities:
    NC_APP = None

NC_TO_TEST = []
if NC:
    NC_TO_TEST.append(NC)
if NC_APP:
    NC_TO_TEST.append(NC_APP)

NC_VERSION = NC_TO_TEST[0].srv_version if NC_TO_TEST else {}
