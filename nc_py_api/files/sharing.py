"""Nextcloud API for working with the files shares."""

import typing

from .. import _misc, _session
from . import FilePermissions, FsNode, Share, ShareType


class _FilesSharingAPI:
    """Class provides all File Sharing functionality."""

    _ep_base: str = "/ocs/v1.php/apps/files_sharing/api/v1"

    def __init__(self, session: _session.NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not _misc.check_capabilities("files_sharing.api_enabled", self._session.capabilities)

    def get_list(
        self, shared_with_me=False, reshares=False, subfiles=False, path: typing.Union[str, FsNode] = ""
    ) -> list[Share]:
        """Returns lists of shares.

        :param shared_with_me: Shares should be with the current user.
        :param reshares: Only get shares by the current user and reshares.
        :param subfiles: Only get all sub shares in a folder.
        :param path: Get shares for a specific path.
        """
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
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
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        result = self._session.ocs(method="GET", path=f"{self._ep_base}/shares/{share_id}")
        return Share(result[0] if isinstance(result, list) else result)

    def get_inherited(self, path: str) -> list[Share]:
        """Get all shares relative to a file, e.g., parent folders shares."""
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        result = self._session.ocs(method="GET", path=f"{self._ep_base}/shares/inherited", params={"path": path})
        return [Share(i) for i in result]

    def create(
        self,
        path: typing.Union[str, FsNode],
        share_type: ShareType,
        permissions: typing.Optional[FilePermissions] = None,
        share_with: str = "",
        **kwargs,
    ) -> Share:
        """Creates a new share.

        :param path: The path of an existing file/directory.
        :param share_type: :py:class:`~nc_py_api.files.sharing.ShareType` value.
        :param permissions: combination of the :py:class:`~nc_py_api.files.FilePermissions` values.
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
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        params = {
            "path": path.user_path if isinstance(path, FsNode) else path,
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
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
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
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="DELETE", path=f"{self._ep_base}/shares/{share_id}")

    def get_pending(self) -> list[Share]:
        """Returns all pending shares for current user."""
        return [Share(i) for i in self._session.ocs(method="GET", path=f"{self._ep_base}/shares/pending")]

    def accept_share(self, share_id: typing.Union[int, Share]) -> None:
        """Accept pending share."""
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="POST", path=f"{self._ep_base}/pending/{share_id}")

    def decline_share(self, share_id: typing.Union[int, Share]) -> None:
        """Decline pending share."""
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="DELETE", path=f"{self._ep_base}/pending/{share_id}")

    def get_deleted(self) -> list[Share]:
        """Get a list of deleted shares."""
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        return [Share(i) for i in self._session.ocs(method="GET", path=f"{self._ep_base}/deletedshares")]

    def undelete(self, share_id: typing.Union[int, Share]) -> None:
        """Undelete a deleted share."""
        _misc.require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        share_id = share_id.share_id if isinstance(share_id, Share) else share_id
        self._session.ocs(method="POST", path=f"{self._ep_base}/deletedshares/{share_id}")
