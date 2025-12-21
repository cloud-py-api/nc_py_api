"""Nextcloud API for working with Group Folders."""

import dataclasses

from ._misc import check_capabilities, clear_from_params_empty, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class GroupFolder:
    """Class representing one group folder."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def folder_id(self) -> int:
        """Unique identifier of the folder."""
        return self._raw_data["id"]

    @property
    def mount_point(self) -> str:
        """Mount point (path) of the folder."""
        return self._raw_data["mount_point"]

    @property
    def groups(self) -> dict[str, int]:
        """Dictionary mapping group IDs to their permission levels."""
        return self._raw_data.get("groups", {})

    @property
    def quota(self) -> int:
        """Quota limit in bytes (-3 for unlimited)."""
        return self._raw_data.get("quota", -3)

    @property
    def size(self) -> int:
        """Current size of the folder in bytes."""
        return self._raw_data.get("size", 0)

    @property
    def acl(self) -> bool:
        """Whether Advanced Permissions (ACL) are enabled."""
        return self._raw_data.get("acl", False)

    @property
    def manage(self) -> str:
        """Who can manage the folder."""
        return self._raw_data.get("manage", "")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.folder_id}, mount_point={self.mount_point}, quota={self.quota}>"


class _GroupFoldersAPI:
    """Class providing an API for managing Group Folders on the Nextcloud server."""

    _ep_base: str = "/apps/groupfolders/folders"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("groupfolders.enabled", self._session.capabilities)

    def get_list(self) -> list[GroupFolder]:
        """Returns a list of all group folders.

        .. note:: The API returns a dictionary with folder IDs as keys, which is converted to a list.
        """
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        result = self._session.ocs("GET", self._ep_base)
        if isinstance(result, dict):
            return [GroupFolder(v) for k, v in result.items()]
        return [GroupFolder(i) for i in result]

    def get(self, folder_id: int) -> GroupFolder:
        """Returns a specific group folder by ID."""
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        folders = self.get_list()
        matching = [f for f in folders if f.folder_id == folder_id]
        if not matching:
            raise ValueError(f"Group folder with ID {folder_id} not found.")
        return matching[0]

    def create(self, mount_point: str) -> GroupFolder:
        """Creates a new group folder.

        :param mount_point: Mount point (path) for the folder.
        """
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        params = {"mountpoint": mount_point}
        result = self._session.ocs("POST", self._ep_base, json=params)
        return GroupFolder(result)

    def delete(self, folder_id: int) -> None:
        """Deletes a group folder."""
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        self._session.ocs("DELETE", f"{self._ep_base}/{folder_id}")

    def set_quota(self, folder_id: int, quota: int) -> None:
        """Sets the quota for a group folder.

        :param folder_id: ID of the folder.
        :param quota: Quota in bytes (-3 for unlimited).
        """
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        params = {"quota": quota}
        self._session.ocs("POST", f"{self._ep_base}/{folder_id}/quota", json=params)

    def set_permissions(self, folder_id: int, group_id: str, permissions: int) -> None:
        """Sets permissions for a group on a folder.

        :param folder_id: ID of the folder.
        :param group_id: ID of the group.
        :param permissions: Permission bitmask (1=Read, 2=Write, 4=Create, 8=Delete, 16=Share, 31=All).
        """
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        params = {"permissions": permissions}
        self._session.ocs("POST", f"{self._ep_base}/{folder_id}/groups/{group_id}", json=params)

    def remove_group(self, folder_id: int, group_id: str) -> None:
        """Removes a group from a folder."""
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        self._session.ocs("DELETE", f"{self._ep_base}/{folder_id}/groups/{group_id}")

    def set_acl(self, folder_id: int, acl: bool) -> None:
        """Enables or disables Advanced Permissions (ACL) for a folder.

        :param folder_id: ID of the folder.
        :param acl: True to enable ACL, False to disable.
        """
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        params = {"acl": 1 if acl else 0}
        self._session.ocs("POST", f"{self._ep_base}/{folder_id}/acl", json=params)

    def set_acl_permission(self, folder_id: int, mapping_id: str, mapping_type: str, permissions: int) -> None:
        """Sets ACL permission for a user or group on a folder.

        :param folder_id: ID of the folder.
        :param mapping_id: User or group ID.
        :param mapping_type: Type of mapping ('user' or 'group').
        :param permissions: Permission bitmask (1=Read, 2=Write, 4=Create, 8=Delete, 16=Share, 31=All).
        """
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        params = {"mappingType": mapping_type, "mappingId": mapping_id, "permissions": permissions}
        self._session.ocs("POST", f"{self._ep_base}/{folder_id}/acl", json=params)

    def remove_acl_permission(self, folder_id: int, mapping_id: str, mapping_type: str) -> None:
        """Removes ACL permission for a user or group from a folder.

        :param folder_id: ID of the folder.
        :param mapping_id: User or group ID.
        :param mapping_type: Type of mapping ('user' or 'group').
        """
        require_capabilities("groupfolders.enabled", self._session.capabilities)
        params = {"mappingType": mapping_type, "mappingId": mapping_id}
        self._session.ocs("DELETE", f"{self._ep_base}/{folder_id}/acl", json=params)


class _AsyncGroupFoldersAPI:
    """Class provides async API for managing Group Folders on the Nextcloud server."""

    _ep_base: str = "/apps/groupfolders/folders"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("groupfolders.enabled", await self._session.capabilities)

    async def get_list(self) -> list[GroupFolder]:
        """Returns a list of all group folders.

        .. note:: The API returns a dictionary with folder IDs as keys, which is converted to a list.
        """
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        result = await self._session.ocs("GET", self._ep_base)
        if isinstance(result, dict):
            return [GroupFolder(v) for k, v in result.items()]
        return [GroupFolder(i) for i in result]

    async def get(self, folder_id: int) -> GroupFolder:
        """Returns a specific group folder by ID."""
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        folders = await self.get_list()
        matching = [f for f in folders if f.folder_id == folder_id]
        if not matching:
            raise ValueError(f"Group folder with ID {folder_id} not found.")
        return matching[0]

    async def create(self, mount_point: str) -> GroupFolder:
        """Creates a new group folder.

        :param mount_point: Mount point (path) for the folder.
        """
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        params = {"mountpoint": mount_point}
        result = await self._session.ocs("POST", self._ep_base, json=params)
        return GroupFolder(result)

    async def delete(self, folder_id: int) -> None:
        """Deletes a group folder."""
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/{folder_id}")

    async def set_quota(self, folder_id: int, quota: int) -> None:
        """Sets the quota for a group folder.

        :param folder_id: ID of the folder.
        :param quota: Quota in bytes (-3 for unlimited).
        """
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        params = {"quota": quota}
        await self._session.ocs("POST", f"{self._ep_base}/{folder_id}/quota", json=params)

    async def set_permissions(self, folder_id: int, group_id: str, permissions: int) -> None:
        """Sets permissions for a group on a folder.

        :param folder_id: ID of the folder.
        :param group_id: ID of the group.
        :param permissions: Permission bitmask (1=Read, 2=Write, 4=Create, 8=Delete, 16=Share, 31=All).
        """
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        params = {"permissions": permissions}
        await self._session.ocs("POST", f"{self._ep_base}/{folder_id}/groups/{group_id}", json=params)

    async def remove_group(self, folder_id: int, group_id: str) -> None:
        """Removes a group from a folder."""
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/{folder_id}/groups/{group_id}")

    async def set_acl(self, folder_id: int, acl: bool) -> None:
        """Enables or disables Advanced Permissions (ACL) for a folder.

        :param folder_id: ID of the folder.
        :param acl: True to enable ACL, False to disable.
        """
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        params = {"acl": 1 if acl else 0}
        await self._session.ocs("POST", f"{self._ep_base}/{folder_id}/acl", json=params)

    async def set_acl_permission(self, folder_id: int, mapping_id: str, mapping_type: str, permissions: int) -> None:
        """Sets ACL permission for a user or group on a folder.

        :param folder_id: ID of the folder.
        :param mapping_id: User or group ID.
        :param mapping_type: Type of mapping ('user' or 'group').
        :param permissions: Permission bitmask (1=Read, 2=Write, 4=Create, 8=Delete, 16=Share, 31=All).
        """
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        params = {"mappingType": mapping_type, "mappingId": mapping_id, "permissions": permissions}
        await self._session.ocs("POST", f"{self._ep_base}/{folder_id}/acl", json=params)

    async def remove_acl_permission(self, folder_id: int, mapping_id: str, mapping_type: str) -> None:
        """Removes ACL permission for a user or group from a folder.

        :param folder_id: ID of the folder.
        :param mapping_id: User or group ID.
        :param mapping_type: Type of mapping ('user' or 'group').
        """
        require_capabilities("groupfolders.enabled", await self._session.capabilities)
        params = {"mappingType": mapping_type, "mappingId": mapping_id}
        await self._session.ocs("DELETE", f"{self._ep_base}/{folder_id}/acl", json=params)
