"""
Options to change nc_py_api's runtime behaviour.
"""

XDEBUG_SESSION = "PHPSTORM"
"""Dev option, for debugging PHP code"""

TIMEOUT = 50
"""Default timeout for OCS API calls. Set to "None" to disable timeouts for development."""

TIMEOUT_DAV = TIMEOUT * 3 if TIMEOUT else None
"""File operations timeout, usually it is OCS timeout multiplied by 3."""

VERIFY_NC_CERTIFICATE = True
"""Option to enable/disable Nextcloud certificate verification

In the case of self-signed certificates, you can disable verification."""
