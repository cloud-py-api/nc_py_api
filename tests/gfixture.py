from os import environ

import gfixture_set_env  # noqa

from nc_py_api import Nextcloud, NextcloudApp

NC = None if environ.get("SKIP_NC_CLIENT_TESTS", False) else Nextcloud()

if environ.get("SKIP_AE_TESTS", False):
    NC_APP = None
else:
    NC_APP = NextcloudApp(user="admin")
    if "app_ecosystem_v2" not in NC_APP.capabilities:
        NC_APP = None

NC_TO_TEST = []
if NC:
    NC_TO_TEST.append(NC)
if NC_APP:
    NC_TO_TEST.append(NC_APP)

NC_VERSION = NC_TO_TEST[0].srv_version if NC_TO_TEST else {}
