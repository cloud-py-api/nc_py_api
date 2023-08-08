"""Options to change nc_py_api's runtime behavior.

Each setting only affects newly created instances of Nextcloud or NextcloudApp class, unless otherwise specified.
Specifying options in **kwargs** has higher priority than this.
"""
from os import environ

from dotenv import load_dotenv

load_dotenv()

XDEBUG_SESSION = environ.get("XDEBUG_SESSION", "")
"""Dev option, for debugging PHP code."""

NPA_TIMEOUT = environ.get("NPA_TIMEOUT", 50)
"""Default timeout for OCS API calls. Set to ``None`` to disable timeouts for development."""

NPA_TIMEOUT_DAV = environ.get("NPA_TIMEOUT_DAV", NPA_TIMEOUT * 3 if isinstance(NPA_TIMEOUT, int) else None)
"""File operations timeout, usually it is OCS timeout multiplied by 3."""

NPA_NC_CERT = environ.get("NPA_NC_CERT", True)
"""Option to enable/disable Nextcloud certificate verification.

SSL certificates (a.k.a CA bundle) used to  verify the identity of requested hosts. Either **True** (default CA bundle),
a path to an SSL certificate file, or **False** (which will disable verification)."""
