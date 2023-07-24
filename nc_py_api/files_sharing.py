"""
Nextcloud API for working with files shares.
"""

from typing import Union

from ._session import NcSessionBasic
from .constants import SharePermissions, ShareType
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

    def create(
        self,
        path: Union[str, FsNode],
        permissions: SharePermissions,
        share_type: ShareType,
        share_with: str,
        **kwargs,
    ):
        """Creates a new share.

        :param path: The path of an existing file/directory.
        :param permissions: combination of the :py:class:`~nc_py_api.SharePermissions` object values.
        :param share_type: :py:class:`~nc_py_api.ShareType` value.
        :param share_with: string representing object name to where send share.
        :param kwargs: *Additionally supported arguments*

        Additionally supported arguments:
            ``public`` - boolean indicating should share be available for non-registered users.
                default = ``False``
            ``password`` - string with password to protect share.
                default = ``""``
            ``sendPasswordByTalk`` - boolean indicating should password be automatically delivered using Talk.
                default = ``False``
            ``expireDate`` - to-do, choose format.
            ``note`` - string with note, if any.
                default = ``""``
            ``label`` - string with label, if any.
                default = ``""``
        """

        pass  # noqa # pylint: disable=unnecessary-pass
