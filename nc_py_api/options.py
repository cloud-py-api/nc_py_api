"""
Options to change nc_py_api's runtime behaviour.
"""

XDEBUG_SESSION = "PHPSTORM"

TIMEOUT = 50

TIMEOUT_DAV = TIMEOUT * 3 if TIMEOUT else None

DAV_URL_SUFFIX = "/remote.php/dav"
