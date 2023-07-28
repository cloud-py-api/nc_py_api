"""
Nextcloud API for working with the files shares.
"""

from typing import Union

from ._session import NcSessionBasic
from .constants import SharePermissions, ShareType
from .files import FsNode
from .misc import check_capabilities, require_capabilities

ENDPOINT_BASE = "/ocs/v1.php/apps/files_sharing/api/v1/"


class Share:
    """Class represents one Nextcloud Share."""

    def __init__(self, raw_data: dict):
        self.raw_data = raw_data

    @property
    def share_id(self) -> int:
        return int(self.raw_data["id"])

    @property
    def type(self) -> ShareType:
        return ShareType(int(self.raw_data["share_type"]))

    @property
    def permissions(self) -> SharePermissions:
        """Recipient permissions"""

        return SharePermissions(int(self.raw_data["permissions"]))

    @property
    def url(self) -> str:
        return self.raw_data.get("url", "")

    @property
    def path(self) -> str:
        return self.raw_data.get("path", "")

    @property
    def label(self) -> str:
        return self.raw_data.get("label", "")

    @property
    def note(self) -> str:
        return self.raw_data.get("note", "")

    @property
    def mimetype(self) -> str:
        return self.raw_data.get("mimetype", "")


class FilesSharingAPI:
    """This class provides all File Sharing functionality."""

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""

        return not check_capabilities("files_sharing", self._session.capabilities)

    def get_list(
        self, shared_with_me=False, reshares=False, subfiles=False, path: Union[str, FsNode] = ""
    ) -> list[Share]:
        """Returns lists of shares."""

        require_capabilities("files_sharing", self._session.capabilities)
        path = path.user_path if isinstance(path, FsNode) else path
        params = {
            "shared_with_me": "true" if shared_with_me else "false",
            "reshares": "true" if reshares else "false",
            "subfiles": "true" if subfiles else "false",
        }
        if path:
            params["path"] = path
        result = self._session.ocs(method="GET", path=f"{ENDPOINT_BASE}/shares", params=params)
        return [Share(i) for i in result]

    def create(
        self,
        path: Union[str, FsNode],
        permissions: SharePermissions,
        share_type: ShareType,
        share_with: str = "",
        **kwargs,
    ) -> Share:
        """Creates a new share.

        :param path: The path of an existing file/directory.
        :param permissions: combination of the :py:class:`~nc_py_api.SharePermissions` object values.
        :param share_type: :py:class:`~nc_py_api.ShareType` value.
        :param share_with: the recipient of the shared object.
        :param kwargs: See below.

        Additionally supported arguments:

            * ``public`` - boolean indicating should share be available for non-registered users. default = ``False``
            * ``password`` - string with password to protect share. default = ``""``
            * ``send_password_by_talk`` - boolean indicating should password be automatically delivered using Talk.
              default = ``False``
            * ``expire_date`` - :py:class:`~datetime.datetime` time when share should expire.
              `hours, minutes, seconds` are ignored. default = ``None``
            * ``note`` - string with note, if any. default = ``""``
            * ``label`` - string with label, if any. default = ``""``
        """

        require_capabilities("files_sharing", self._session.capabilities)
        path = path.user_path if isinstance(path, FsNode) else path
        params = {
            "path": path,
            "permissions": int(permissions),
            "shareType": int(share_type),
        }
        if share_with:
            kwargs["shareWith"] = share_with
        if kwargs.get("public", False):
            params["publicUpload"] = "true"
        if "password" in kwargs:
            params["publicUpload"] = kwargs["password"]
        if kwargs.get("send_password_by_talk", False):
            params["sendPasswordByTalk"] = "true"
        if "expire_date" in kwargs:
            params["expireDate"] = kwargs["expire_date"].isoformat()
        if "note" in kwargs:
            params["note"] = kwargs["note"]
        if "label" in kwargs:
            params["label"] = kwargs["label"]
        return Share(self._session.ocs(method="POST", path=f"{ENDPOINT_BASE}/shares", params=params))

    def delete(self, share_id: Union[int, Share]) -> None:
        """Removes the given share.

        :param share_id: The Share object or an ID of the share.
        """

        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="DELETE", path=f"{ENDPOINT_BASE}/shares/{share_id}")
