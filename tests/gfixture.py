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

nc = Nextcloud()
nc_app = NextcloudApp(user="admin")
if "app_ecosystem_v2" not in nc_app.capabilities:
    nc_app = None

NC_TO_TEST = [nc]
if nc_app:
    NC_TO_TEST.append(nc_app)

NC_VERSION = nc.srv_version
