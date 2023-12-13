"""Options to change nc_py_api's runtime behavior.

Each setting only affects newly created instances of **Nextcloud**/**NextcloudApp** class, unless otherwise specified.
Specifying options in **kwargs** has higher priority than this.
"""

from os import environ

from dotenv import load_dotenv

load_dotenv()

XDEBUG_SESSION = environ.get("XDEBUG_SESSION", "")
"""Dev option, for debugging PHP code."""

NPA_TIMEOUT: int | None
"""Default timeout for OCS API calls. Set to ``None`` to disable timeouts for development."""
try:
    NPA_TIMEOUT = int(environ.get("NPA_TIMEOUT", 30))
except (TypeError, ValueError):
    NPA_TIMEOUT = None

NPA_TIMEOUT_DAV: int | None
"""File operations timeout, usually it is OCS timeout multiplied by 3."""
try:
    NPA_TIMEOUT_DAV = int(environ.get("NPA_TIMEOUT_DAV", 30 * 3))
except (TypeError, ValueError):
    NPA_TIMEOUT_DAV = None

NPA_NC_CERT: bool | str
"""Option to enable/disable Nextcloud certificate verification.

SSL certificates (a.k.a CA bundle) used to  verify the identity of requested hosts. Either **True** (default CA bundle),
a path to an SSL certificate file, or **False** (which will disable verification)."""
str_val = environ.get("NPA_NC_CERT", "True")
NPA_NC_CERT = True
if str_val.lower() in ("false", "0"):
    NPA_NC_CERT = False
elif str_val.lower() not in ("true", "1"):
    NPA_NC_CERT = str_val

CHUNKED_UPLOAD_V2 = environ.get("CHUNKED_UPLOAD_V2", True)
"""Option to enable/disable **version 2** chunked upload(better Object Storages support).

Additional information can be found in Nextcloud documentation:
`Chunked file upload V2
<https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/chunking.html#chunked-upload-v2>`_"""
