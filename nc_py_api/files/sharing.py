"""Nextcloud API for working with the files shares."""
import datetime
import enum
import typing

from .. import _misc, _session
from . import FsNode


class SharePermissions(enum.IntFlag):
    """The share permissions to be set."""

    PERMISSION_READ = 1
    """Access to read"""
    PERMISSION_UPDATE = 2
    """Access to write"""
    PERMISSION_CREATE = 4
    """Access to create new objects in the share"""
    PERMISSION_DELETE = 8
    """Access to remove objects in the share"""
    PERMISSION_SHARE = 16
    """Access to re-share objects in the share"""


class ShareType(enum.IntEnum):
    """Type of the object that will receive share."""

    TYPE_USER = 0
    """Share to the user"""
    TYPE_GROUP = 1
    """Share to the group"""
    TYPE_LINK = 3
    """Share by link"""
    TYPE_EMAIL = 4
    """Share by the email"""
    TYPE_REMOTE = 6
    """Share to the Federation"""
    TYPE_CIRCLE = 7
    """Share to the Nextcloud Circle"""
    TYPE_GUEST = 8
    """Share to `Guest`"""
    TYPE_REMOTE_GROUP = 9
    """Share to the Federation group"""
    TYPE_ROOM = 10
    """Share to the Talk room"""
    TYPE_DECK = 11
    """Share to the Nextcloud Deck"""
    TYPE_SCIENCE_MESH = 15
    """Share to the Reva instance(Science Mesh)"""


class ShareStatus(enum.IntEnum):
    """Status of the share."""

    STATUS_PENDING = 0
    """The share waits for acceptance"""
    STATUS_ACCEPTED = 1
    """The share was for accepted"""
    STATUS_REJECTED = 2
    """The share was for rejected"""


class Share:
    """Information about Share."""

    def __init__(self, raw_data: dict):
        self.raw_data = raw_data

    @property
    def share_id(self) -> int:
        """Unique ID of the share."""
        return int(self.raw_data["id"])

    @property
    def share_type(self) -> ShareType:
        """Type of the share."""
        return ShareType(int(self.raw_data["share_type"]))

    @property
    def share_with(self) -> str:
        """To whom Share was created."""
        return self.raw_data["share_with"]

    @property
    def permissions(self) -> SharePermissions:
        """Recipient permissions."""
        return SharePermissions(int(self.raw_data["permissions"]))

    @property
    def url(self) -> str:
        """URL at which Share is avalaible."""
        return self.raw_data.get("url", "")

    @property
    def path(self) -> str:
        """Share path relative to the user's root directory."""
        return self.raw_data.get("path", "").lstrip("/")

    @property
    def label(self) -> str:
        """Label for the Shared object."""
        return self.raw_data.get("label", "")

    @property
    def note(self) -> str:
        """Note for the Shared object."""
        return self.raw_data.get("note", "")

    @property
    def mimetype(self) -> str:
        """Mimetype of the Shared object."""
        return self.raw_data.get("mimetype", "")

    @property
    def share_owner(self) -> str:
        """Share's creator ID."""
        return self.raw_data.get("uid_owner", "")

    @property
    def file_owner(self) -> str:
        """File/directory owner ID."""
        return self.raw_data.get("uid_file_owner", "")

    @property
    def password(self) -> str:
        """Password to access share."""
        return self.raw_data.get("password", "")

    @property
    def send_password_by_talk(self) -> bool:
        """Flag indicating was password send by Talk."""
        return self.raw_data.get("send_password_by_talk", False)

    @property
    def expire_date(self) -> datetime.datetime:
        """Share expiration time."""
        try:
            return datetime.datetime.fromisoformat(self.raw_data["expiration"])
        except (ValueError, TypeError, KeyError):
            return datetime.datetime(1970, 1, 1)

    def __str__(self):
        return (
            f"{self.share_type.name}: `{self.path}` with id={self.share_id}"
            f" from {self.share_owner} to {self.share_with}"
        )


class _FilesSharingAPI:
    """Class provides all File Sharing functionality."""

    _ep_base: str = "/ocs/v1.php/apps/files_sharing/api/v1"

    def __init__(self, session: _session.NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not _misc.check_capabilities("files_sharing", self._session.capabilities)

    def get_list(
        self, shared_with_me=False, reshares=False, subfiles=False, path: typing.Union[str, FsNode] = ""
    ) -> list[Share]:
        """Returns lists of shares.

        :param shared_with_me: Shares should be with the current user.
        :param reshares: Only get shares by the current user and reshares.
        :param subfiles: Only get all sub shares in a folder.
        :param path: Get shares for a specific path.
        """
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        path = path.user_path if isinstance(path, FsNode) else path
        params = {
            "shared_with_me": "true" if shared_with_me else "false",
            "reshares": "true" if reshares else "false",
            "subfiles": "true" if subfiles else "false",
        }
        if path:
            params["path"] = path
        result = self._session.ocs(method="GET", path=f"{self._ep_base}/shares", params=params)
        return [Share(i) for i in result]

    def get_by_id(self, share_id: int) -> Share:
        """Get Share by share ID."""
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        result = self._session.ocs(method="GET", path=f"{self._ep_base}/shares/{share_id}")
        return Share(result[0] if isinstance(result, list) else result)

    def get_inherited(self, path: str) -> list[Share]:
        """Get all shares relative to a file, e.g., parent folders shares."""
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        result = self._session.ocs(method="GET", path=f"{self._ep_base}/shares/inherited", params={"path": path})
        return [Share(i) for i in result]

    def create(
        self,
        path: typing.Union[str, FsNode],
        share_type: ShareType,
        permissions: typing.Optional[SharePermissions] = None,
        share_with: str = "",
        **kwargs,
    ) -> Share:
        """Creates a new share.

        :param path: The path of an existing file/directory.
        :param share_type: :py:class:`~nc_py_api.files.sharing.ShareType` value.
        :param permissions: combination of the :py:class:`~nc_py_api.files.sharing.SharePermissions` object values.
        :param share_with: the recipient of the shared object.
        :param kwargs: See below.

        Additionally supported arguments:

            * ``public_upload`` - indicating should share be available for upload for non-registered users.
              default = ``False``
            * ``password`` - string with password to protect share. default = ``""``
            * ``send_password_by_talk`` - boolean indicating should password be automatically delivered using Talk.
              default = ``False``
            * ``expire_date`` - :py:class:`~datetime.datetime` time when share should expire.
              `hours, minutes, seconds` are ignored. default = ``None``
            * ``note`` - string with note, if any. default = ``""``
            * ``label`` - string with label, if any. default = ``""``
        """
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        path = path.user_path if isinstance(path, FsNode) else path
        params = {
            "path": path,
            "shareType": int(share_type),
        }
        if permissions is not None:
            params["permissions"] = int(permissions)
        if share_with:
            params["shareWith"] = share_with
        if kwargs.get("public_upload", False):
            params["publicUpload"] = "true"
        if "password" in kwargs:
            params["password"] = kwargs["password"]
        if kwargs.get("send_password_by_talk", False):
            params["sendPasswordByTalk"] = "true"
        if "expire_date" in kwargs:
            params["expireDate"] = kwargs["expire_date"].isoformat()
        if "note" in kwargs:
            params["note"] = kwargs["note"]
        if "label" in kwargs:
            params["label"] = kwargs["label"]
        return Share(self._session.ocs(method="POST", path=f"{self._ep_base}/shares", params=params))

    def update(self, share_id: typing.Union[int, Share], **kwargs) -> Share:
        """Updates the share options.

        :param share_id: ID of the Share to update.
        :param kwargs: Available for update: ``permissions``, ``password``, ``send_password_by_talk``,
          ``public_upload``, ``expire_date``, ``note``, ``label``.
        """
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        params: dict = {}
        if "permissions" in kwargs:
            params["permissions"] = int(kwargs["permissions"])
        if "password" in kwargs:
            params["password"] = kwargs["password"]
        if kwargs.get("send_password_by_talk", False):
            params["sendPasswordByTalk"] = "true"
        if kwargs.get("public_upload", False):
            params["publicUpload"] = "true"
        if "expire_date" in kwargs:
            params["expireDate"] = kwargs["expire_date"].isoformat()
        if "note" in kwargs:
            params["note"] = kwargs["note"]
        if "label" in kwargs:
            params["label"] = kwargs["label"]
        return Share(self._session.ocs(method="PUT", path=f"{self._ep_base}/shares/{share_id}", params=params))

    def delete(self, share_id: typing.Union[int, Share]) -> None:
        """Removes the given share.

        :param share_id: The Share object or an ID of the share.
        """
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="DELETE", path=f"{self._ep_base}/shares/{share_id}")

    def get_pending(self) -> list[Share]:
        """Returns all pending shares for current user."""
        return [Share(i) for i in self._session.ocs(method="GET", path=f"{self._ep_base}/shares/pending")]

    def accept_share(self, share_id: typing.Union[int, Share]):
        """Accept pending share."""
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="POST", path=f"{self._ep_base}/pending/{share_id}")

    def decline_share(self, share_id: typing.Union[int, Share]):
        """Decline pending share."""
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="DELETE", path=f"{self._ep_base}/pending/{share_id}")

    def get_deleted(self) -> list[Share]:
        """Get a list of deleted shares."""
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        return [Share(i) for i in self._session.ocs(method="GET", path=f"{self._ep_base}/deletedshares")]

    def undelete(self, share_id: typing.Union[int, Share]) -> None:
        """Undelete a deleted share."""
        _misc.require_capabilities("files_sharing", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="POST", path=f"{self._ep_base}/deletedshares/{share_id}")
