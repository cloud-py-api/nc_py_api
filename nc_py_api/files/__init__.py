"""APIs related to Files and Shares."""

import dataclasses
import datetime
import email.utils
import enum
import os
import warnings

from pydantic import BaseModel

from .. import _misc


class LockType(enum.IntEnum):
    """Nextcloud File Locks types."""

    MANUAL_LOCK = 0
    COLLABORATIVE_LOCK = 1
    WEBDAV_TOKEN = 2


@dataclasses.dataclass
class FsNodeLockInfo:
    """File Lock information if Nextcloud `files_lock` is enabled."""

    def __init__(self, **kwargs):
        self._is_locked = bool(int(kwargs.get("is_locked", False)))
        self._lock_owner_type = LockType(int(kwargs.get("lock_owner_type", 0)))
        self._lock_owner = kwargs.get("lock_owner", "")
        self._owner_display_name = kwargs.get("owner_display_name", "")
        self._owner_editor = kwargs.get("lock_owner_editor", "")
        self._lock_time = int(kwargs.get("lock_time", 0))
        self._lock_ttl = int(kwargs.get("_lock_ttl", 0))

    @property
    def is_locked(self) -> bool:
        """Returns ``True`` if the file is locked, ``False`` otherwise."""
        return self._is_locked

    @property
    def type(self) -> LockType:
        """Type of the lock."""
        return LockType(self._lock_owner_type)

    @property
    def owner(self) -> str:
        """User id of the lock owner."""
        return self._lock_owner

    @property
    def owner_display_name(self) -> str:
        """Display name of the lock owner."""
        return self._owner_display_name

    @property
    def owner_editor(self) -> str:
        """App id of an app owned lock to allow clients to suggest joining the collaborative editing session."""
        return self._owner_editor

    @property
    def lock_creation_time(self) -> datetime.datetime:
        """Lock creation time."""
        return datetime.datetime.utcfromtimestamp(self._lock_time).replace(tzinfo=datetime.timezone.utc)

    @property
    def lock_ttl(self) -> int:
        """TTL of the lock in seconds staring from the creation time. A value of 0 means the timeout is infinite."""
        return self._lock_ttl


@dataclasses.dataclass
class FsNodeInfo:
    """Extra FS object attributes from Nextcloud."""

    fileid: int
    """Clear file ID without Nextcloud instance ID."""
    favorite: bool
    """Flag indicating if the object is marked as favorite."""
    is_version: bool
    """Flag indicating if the object is File Version representation"""
    _last_modified: datetime.datetime
    _trashbin: dict

    def __init__(self, **kwargs):
        self._raw_data = {
            "content_length": kwargs.get("content_length", 0),
            "size": kwargs.get("size", 0),
            "permissions": kwargs.get("permissions", ""),
            "mimetype": kwargs.get("mimetype", ""),
        }
        self.favorite = kwargs.get("favorite", False)
        self.is_version = False
        self.fileid = kwargs.get("fileid", 0)
        try:
            self.last_modified = kwargs.get("last_modified", datetime.datetime(1970, 1, 1))
        except (ValueError, TypeError):
            self.last_modified = datetime.datetime(1970, 1, 1)
        self._trashbin: dict[str, str | int] = {}
        for i in ("trashbin_filename", "trashbin_original_location", "trashbin_deletion_time"):
            if i in kwargs:
                self._trashbin[i] = kwargs[i]

    @property
    def content_length(self) -> int:
        """Length of file in bytes, zero for directories."""
        return self._raw_data["content_length"]

    @property
    def size(self) -> int:
        """In the case of directories it is the size of all content, for files it is equal to ``content_length``."""
        return self._raw_data["size"]

    @property
    def mimetype(self) -> str:
        """Mimetype of a file. Empty for the directories."""
        return self._raw_data["mimetype"]

    @property
    def permissions(self) -> str:
        """Permissions for the object."""
        return self._raw_data["permissions"]

    @property
    def last_modified(self) -> datetime.datetime:
        """Time when the object was last modified.

        .. note:: ETag is a more preferable way to check if the object was changed.
        """
        return self._last_modified

    @last_modified.setter
    def last_modified(self, value: str | datetime.datetime):
        if isinstance(value, str):
            self._last_modified = email.utils.parsedate_to_datetime(value)
        else:
            self._last_modified = value

    @property
    def in_trash(self) -> bool:
        """Returns ``True`` if the object is in trash."""
        return bool(self._trashbin)

    @property
    def trashbin_filename(self) -> str:
        """Returns the name of the object in the trashbin."""
        return self._trashbin.get("trashbin_filename", "")

    @property
    def trashbin_original_location(self) -> str:
        """Returns the original path of the object."""
        return self._trashbin.get("trashbin_original_location", "")

    @property
    def trashbin_deletion_time(self) -> int:
        """Returns deletion time of the object."""
        return int(self._trashbin.get("trashbin_deletion_time", 0))


@dataclasses.dataclass
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

    lock_info: FsNodeLockInfo
    """Class describing `lock` information if any."""

    def __init__(self, full_path: str, **kwargs):
        self.full_path = full_path
        self.file_id = kwargs.get("file_id", "")
        self.etag = kwargs.get("etag", "")
        self.info = FsNodeInfo(**kwargs)
        self.lock_info = FsNodeLockInfo(**kwargs)

    @property
    def is_dir(self) -> bool:
        """Returns ``True`` for the directories, ``False`` otherwise."""
        return self.full_path.endswith("/")

    def __str__(self):
        if self.info.is_version:
            return (
                f"File version: `{self.name}` for FileID={self.file_id}"
                f" last modified at {self.info.last_modified} with {self.info.content_length} bytes size."
            )
        return (
            f"{'Dir' if self.is_dir else 'File'}: `{self.name}` with id={self.file_id}"
            f" last modified at {self.info.last_modified} and {self.info.permissions} permissions."
        )

    def __eq__(self, other):
        return bool(self.file_id and self.file_id == other.file_id)

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


class FilePermissions(enum.IntFlag):
    """List of available permissions for files/directories."""

    PERMISSION_READ = 1
    """Access to read"""
    PERMISSION_UPDATE = 2
    """Access to write"""
    PERMISSION_CREATE = 4
    """Access to create new objects in the directory"""
    PERMISSION_DELETE = 8
    """Access to remove object(s)"""
    PERMISSION_SHARE = 16
    """Access to re-share object(s)"""


def permissions_to_str(permissions: int | str, is_dir: bool = False) -> str:
    """Converts integer permissions to string permissions.

    :param permissions: concatenation of ``FilePermissions`` integer flags.
    :param is_dir: Flag indicating is permissions related to the directory object or not.
    """
    permissions = int(permissions) if not isinstance(permissions, int) else permissions
    r = ""
    if permissions & FilePermissions.PERMISSION_SHARE:
        r += "R"
    if permissions & FilePermissions.PERMISSION_READ:
        r += "G"
    if permissions & FilePermissions.PERMISSION_DELETE:
        r += "D"
    if permissions & FilePermissions.PERMISSION_UPDATE:
        r += "NV" if is_dir else "NVW"
    if is_dir and permissions & FilePermissions.PERMISSION_CREATE:
        r += "CK"
    return r


@dataclasses.dataclass
class SystemTag:
    """Nextcloud System Tag."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def tag_id(self) -> int:
        """Unique numeric identifier of the Tag."""
        return int(self._raw_data["oc:id"])

    @property
    def display_name(self) -> str:
        """The visible Tag name."""
        return self._raw_data.get("oc:display-name", str(self.tag_id))

    @property
    def user_visible(self) -> bool:
        """Flag indicating if the Tag is visible in the UI."""
        return bool(self._raw_data.get("oc:user-visible", "false").lower() == "true")

    @property
    def user_assignable(self) -> bool:
        """Flag indicating if User can assign this Tag."""
        return bool(self._raw_data.get("oc:user-assignable", "false").lower() == "true")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.tag_id}, name={self.display_name}>"


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


class Share:
    """Information about Share."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    def __getattr__(self, name):
        if name == "raw_data":
            warnings.warn(
                f"{name} is deprecated and will be removed in 0.10.0 version.", DeprecationWarning, stacklevel=2
            )
            return self._raw_data
        return getattr(self, name)

    @property
    def share_id(self) -> int:
        """Unique ID of the share."""
        return int(self._raw_data["id"])

    @property
    def share_type(self) -> ShareType:
        """Type of the share."""
        return ShareType(int(self._raw_data["share_type"]))

    @property
    def share_with(self) -> str:
        """To whom Share was created."""
        return self._raw_data["share_with"]

    @property
    def permissions(self) -> FilePermissions:
        """Recipient permissions."""
        return FilePermissions(int(self._raw_data["permissions"]))

    @property
    def url(self) -> str:
        """URL at which Share is avalaible."""
        return self._raw_data.get("url", "")

    @property
    def path(self) -> str:
        """Share path relative to the user's root directory."""
        return self._raw_data.get("path", "").lstrip("/")

    @property
    def label(self) -> str:
        """Label for the Shared object."""
        return self._raw_data.get("label", "")

    @property
    def note(self) -> str:
        """Note for the Shared object."""
        return self._raw_data.get("note", "")

    @property
    def mimetype(self) -> str:
        """Mimetype of the Shared object."""
        return self._raw_data.get("mimetype", "")

    @property
    def share_owner(self) -> str:
        """Share's creator ID."""
        return self._raw_data.get("uid_owner", "")

    @property
    def file_owner(self) -> str:
        """File/directory owner ID."""
        return self._raw_data.get("uid_file_owner", "")

    @property
    def password(self) -> str:
        """Password to access share."""
        return self._raw_data.get("password", "")

    @property
    def send_password_by_talk(self) -> bool:
        """Flag indicating was password send by Talk."""
        return self._raw_data.get("send_password_by_talk", False)

    @property
    def expire_date(self) -> datetime.datetime:
        """Share expiration time."""
        return _misc.nc_iso_time_to_datetime(self._raw_data.get("expiration", ""))

    @property
    def file_source_id(self) -> int:
        """File source ID."""
        return self._raw_data.get("file_source", 0)

    @property
    def can_edit(self) -> bool:
        """Does caller have ``write`` permissions."""
        return self._raw_data.get("can_edit", False)

    @property
    def can_delete(self) -> bool:
        """Does caller have ``delete`` permissions."""
        return self._raw_data.get("can_delete", False)

    def __str__(self):
        return (
            f"{self.share_type.name}: `{self.path}` with id={self.share_id}"
            f" from {self.share_owner} to {self.share_with}"
        )


class ActionFileInfo(BaseModel):
    """Information Nextcloud sends to the External Application about File Nodes affected in action."""

    fileId: int
    """FileID without Nextcloud instance ID"""
    name: str
    """Name of the file/directory"""
    directory: str
    """Directory relative to the user's home directory"""
    etag: str
    mime: str
    fileType: str
    """**file** or **dir**"""
    size: int
    """size of file/directory"""
    favorite: str
    """**true** or **false**"""
    permissions: int
    """Combination of :py:class:`~nc_py_api.files.FilePermissions` values"""
    mtime: int
    """Last modified time"""
    userId: str
    """The ID of the user performing the action."""
    shareOwner: str | None = None
    """If the object is shared, this is a display name of the share owner."""
    shareOwnerId: str | None = None
    """If the object is shared, this is the owner ID of the share."""
    instanceId: str | None = None
    """Nextcloud instance ID."""

    def to_fs_node(self) -> FsNode:
        """Returns usual :py:class:`~nc_py_api.files.FsNode` created from this class."""
        user_path = os.path.join(self.directory, self.name).rstrip("/")
        is_dir = bool(self.fileType.lower() == "dir")
        if is_dir:
            user_path += "/"
        full_path = os.path.join(f"files/{self.userId}", user_path.lstrip("/"))
        file_id = str(self.fileId).rjust(8, "0")

        permissions = "S" if self.shareOwnerId else ""
        permissions += permissions_to_str(self.permissions, is_dir)
        return FsNode(
            full_path,
            etag=self.etag,
            size=self.size,
            content_length=0 if is_dir else self.size,
            permissions=permissions,
            favorite=bool(self.favorite.lower() == "true"),
            file_id=file_id + self.instanceId if self.instanceId else file_id,
            fileid=self.fileId,
            last_modified=datetime.datetime.utcfromtimestamp(self.mtime).replace(tzinfo=datetime.timezone.utc),
            mimetype=self.mime,
        )


class ActionFileInfoEx(BaseModel):
    """New ``register_ex`` uses new data format which allowing receiving multiple NC Nodes in one request."""

    files: list[ActionFileInfo]
    """Always list of ``ActionFileInfo`` with one element minimum."""
