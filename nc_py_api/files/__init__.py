"""APIs related to Files and Shares."""

import dataclasses
import datetime
import email.utils
import enum
import typing


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
        }
        self.favorite = kwargs.get("favorite", False)
        self.is_version = False
        self.fileid = kwargs.get("fileid", 0)
        try:
            self.last_modified = kwargs.get("last_modified", datetime.datetime(1970, 1, 1))
        except (ValueError, TypeError):
            self.last_modified = datetime.datetime(1970, 1, 1)
        self._trashbin: dict[str, typing.Union[str, int]] = {}
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
    def last_modified(self, value: typing.Union[str, datetime.datetime]):
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
        if self.info.is_version:
            return (
                f"File version: `{self.name}` for FileID={self.file_id}"
                f" last modified at {str(self.info.last_modified)} with {self.info.content_length} bytes size."
            )
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
