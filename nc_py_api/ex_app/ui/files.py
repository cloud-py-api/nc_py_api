"""Nextcloud API for working with drop-down file's menu."""
import os
import typing
from datetime import datetime, timezone

from pydantic import BaseModel

from ..._exceptions import NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import NcSessionApp
from ...files import FsNode, permissions_to_str


class UiActionFileInfo(BaseModel):
    """File Information Nextcloud sends to the External Application."""

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
    shareOwner: typing.Optional[str]
    """If the object is shared, this is a display name of the share owner."""
    shareOwnerId: typing.Optional[str]
    """If the object is shared, this is the owner ID of the share."""
    instanceId: typing.Optional[str]
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
            last_modified=datetime.utcfromtimestamp(self.mtime).replace(tzinfo=timezone.utc),
            mimetype=self.mime,
        )


class UiFileActionHandlerInfo(BaseModel):
    """Action information Nextcloud sends to the External Application."""

    actionName: str
    """Name of the action, useful when App registers multiple actions for one handler."""
    actionHandler: str
    """Callback url, which was called with this information."""
    actionFile: UiActionFileInfo
    """Information about the file on which the action run."""


class _UiFilesActionsAPI:
    """API for the drop-down menu in Nextcloud **Files app**."""

    _ep_suffix: str = "files/actions/menu"

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(self, name: str, display_name: str, callback_url: str, **kwargs) -> None:
        """Registers the files a dropdown menu element."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "fileActionMenuParams": {
                "name": name,
                "display_name": display_name,
                "mime": kwargs.get("mime", "file"),
                "permissions": kwargs.get("permissions", 31),
                "order": kwargs.get("order", 0),
                "icon": kwargs.get("icon", ""),
                "icon_class": kwargs.get("icon_class", "icon-app-api"),
                "action_handler": callback_url,
            },
        }
        self._session.ocs(method="POST", path=f"{self._session.ae_url}/{self._ep_suffix}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes files dropdown menu element."""
        require_capabilities("app_api", self._session.capabilities)
        params = {"fileActionMenuName": name}
        try:
            self._session.ocs(method="DELETE", path=f"{self._session.ae_url}/{self._ep_suffix}", json=params)
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None
