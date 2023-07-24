"""
Nextcloud API for working with files shares.
"""

from typing import Union

from ._session import NcSessionBasic
from .files import FsNode

ENDPOINT_BASE_SHARES = "/ocs/v1.php/shares"
ENDPOINT_BASE_SHAREES = "/ocs/v1.php/sharees"
ENDPOINT_BASE_DELETED = "/ocs/v1.php/deletedshares"
ENDPOINT_BASE_REMOTE = "/ocs/v1.php/remote_shares"


class FilesSharingAPI:
    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_list(self, shared_with_me=False, reshares=False, subfiles=False, path: Union[str, FsNode] = ""):
        params = {
            "shared_with_me": "true" if shared_with_me else "false",
            "reshares": "true" if reshares else "false",
            "subfiles": "true" if subfiles else "false",
            "path": path,
        }
        return self._session.ocs(method="GET", path=f"{ENDPOINT_BASE_SHARES}", params=params)

    def create(self, path: Union[str, FsNode], permissions):
        pass
