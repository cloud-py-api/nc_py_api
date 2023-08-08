"""Definitions related to Files and File Sharing."""

from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from enum import IntEnum, IntFlag
from typing import Union


@dataclass
class FsNodeInfo:
    """Extra FS object attributes from Nextcloud."""

    size: int
    """Length of file in bytes, zero for directories.."""
    content_length: int
    """For directories it is size of all content in it, for files it is equal to ``size``."""
    permissions: str
    """Permissions for the object."""
    favorite: bool
    """Flag indicating if the object is marked as favorite."""
    fileid: int
    """Clear file ID without Nextcloud instance ID."""
    _last_modified: datetime

    def __init__(self, **kwargs):
        self.size = kwargs.get("size", 0)
        self.content_length = kwargs.get("content_length", 0)
        self.permissions = kwargs.get("permissions", "")
        self.favorite = kwargs.get("favorite", False)
        self.fileid = kwargs.get("fileid", 0)
        try:
            self.last_modified = kwargs.get("last_modified", datetime(1970, 1, 1))
        except (ValueError, TypeError):
            self.last_modified = datetime(1970, 1, 1)

    @property
    def last_modified(self) -> datetime:
        """Time when the object was last modified.

        .. note:: ETag if more preferable way to check if the object was changed.
        """
        return self._last_modified

    @last_modified.setter
    def last_modified(self, value: Union[str, datetime]):
        if isinstance(value, str):
            self._last_modified = parsedate_to_datetime(value)
        else:
            self._last_modified = value


@dataclass
class FsNode:
    """A class that represents a Nextcloud file object.

    Acceptable itself as a ``path`` parameter for the most file APIs.
    """

    full_path: str
    """Path to the object, including the username. Does not include `dav` prefix"""

    file_id: str
    """File ID + NC instance ID"""

    etag: str
    """An entity tag (ETag) of the object"""

    info: FsNodeInfo
    """Additional extra information for the object"""

    def __init__(self, full_path: str, **kwargs):
        self.full_path = full_path
        self.file_id = kwargs.get("file_id", "")
        self.etag = kwargs.get("etag", "")
        self.info = FsNodeInfo(**kwargs)

    @property
    def is_dir(self) -> bool:
        """Returns ``True`` for the directories, ``False`` otherwise."""
        return self.full_path.endswith("/")

    def __str__(self):
        return (
            f"{'Dir' if self.is_dir else 'File'}: `{self.name}` with id={self.file_id}"
            f" last modified at {str(self.info.last_modified)} and {self.info.permissions} permissions."
        )

    def __eq__(self, other):
        if self.file_id and self.file_id == other.file_id:
            return True
        return False

    @property
    def has_extra(self) -> bool:
        """Flag showing that this "FsNode" originates from the mkdir/upload methods and lacks extended information."""
        return bool(self.info.permissions)

    @property
    def name(self) -> str:
        """Returns last ``pathname`` component."""
        return self.full_path.rstrip("/").rsplit("/", maxsplit=1)[-1]

    @property
    def user(self) -> str:
        """Returns user ID extracted from the `full_path`."""
        return self.full_path.lstrip("/").split("/", maxsplit=2)[1]

    @property
    def user_path(self) -> str:
        """Returns path relative to the user's root directory."""
        return self.full_path.lstrip("/").split("/", maxsplit=2)[-1]

    @property
    def is_shared(self) -> bool:
        """Check if a file or folder is shared."""
        return self.info.permissions.find("S") != -1

    @property
    def is_shareable(self) -> bool:
        """Check if a file or folder can be shared."""
        return self.info.permissions.find("R") != -1

    @property
    def is_mounted(self) -> bool:
        """Check if a file or folder is mounted."""
        return self.info.permissions.find("M") != -1

    @property
    def is_readable(self) -> bool:
        """Check if the file or folder is readable."""
        return self.info.permissions.find("G") != -1

    @property
    def is_deletable(self) -> bool:
        """Check if a file or folder can be deleted."""
        return self.info.permissions.find("D") != -1

    @property
    def is_updatable(self) -> bool:
        """Check if file/directory is writable."""
        if self.is_dir:
            return self.info.permissions.find("NV") != -1
        return self.info.permissions.find("W") != -1

    @property
    def is_creatable(self) -> bool:
        """Check whether new files or folders can be created inside this folder."""
        if not self.is_dir:
            return False
        return self.info.permissions.find("CK") != -1


class SharePermissions(IntFlag):
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


class ShareType(IntEnum):
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


class ShareStatus(IntEnum):
    """Status of the share."""

    STATUS_PENDING = 0
    """The share waits for acceptance"""
    STATUS_ACCEPTED = 1
    """The share was for accepted"""
    STATUS_REJECTED = 2
    """The share was for rejected"""


class Share:
    """Class represents one Nextcloud Share."""

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
        return self.raw_data.get("path", "")

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
