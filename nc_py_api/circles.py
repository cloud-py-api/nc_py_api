"""Nextcloud API for working with Circles."""

import dataclasses

from ._exceptions import NextcloudException
from ._misc import check_capabilities, clear_from_params_empty, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class Circle:
    """Class representing one circle."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def circle_id(self) -> str:
        """Unique identifier of the circle."""
        return self._raw_data["id"]

    @property
    def name(self) -> str:
        """Name of the circle."""
        return self._raw_data.get("name", "")

    @property
    def display_name(self) -> str:
        """Display name of the circle."""
        return self._raw_data.get("displayName", "")

    @property
    def circle_type(self) -> int:
        """Type of the circle (1 = Personal, 2 = System, etc.)."""
        return self._raw_data.get("type", 1)

    @property
    def role(self) -> int:
        """Role of the current user in the circle."""
        return self._raw_data.get("role", 0)

    @property
    def owner(self) -> str:
        """User ID of the circle owner."""
        return self._raw_data.get("owner", "")

    @property
    def config(self) -> dict:
        """Configuration of the circle."""
        return self._raw_data.get("config", {})

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.circle_id}, name={self.display_name}, type={self.circle_type}>"


@dataclasses.dataclass
class CircleMember:
    """Class representing one circle member."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def member_id(self) -> str:
        """Unique identifier of the member."""
        return self._raw_data["id"]

    @property
    def display_name(self) -> str:
        """Display name of the member."""
        return self._raw_data.get("displayName", "")

    @property
    def member_type(self) -> int:
        """Type of the member (1 = User, 2 = Group, 3 = Circle, etc.)."""
        return self._raw_data.get("type", 1)

    @property
    def role(self) -> int:
        """Role of the member in the circle."""
        return self._raw_data.get("role", 0)

    @property
    def status(self) -> int:
        """Status of the member (0 = Member, 1 = Invited, etc.)."""
        return self._raw_data.get("status", 0)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.member_id}, display_name={self.display_name}, type={self.member_type}>"


class _CirclesAPI:
    """Class providing the Circles API on the Nextcloud server."""

    _ep_base: str = "/ocs/v2.php/apps/circles/circles"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("circles.enabled", self._session.capabilities)

    def get_list(self) -> list[Circle]:
        """Returns a list of all circles accessible to the current user."""
        require_capabilities("circles.enabled", self._session.capabilities)
        result = self._session.ocs("GET", self._ep_base)
        return [Circle(i) for i in result]

    def get(self, circle_id: str) -> Circle:
        """Returns a specific circle by ID."""
        require_capabilities("circles.enabled", self._session.capabilities)
        return Circle(self._session.ocs("GET", f"{self._ep_base}/{circle_id}"))

    def create(self, name: str, display_name: str = "") -> Circle:
        """Creates a new circle.

        :param name: Name of the circle.
        :param display_name: Display name of the circle (defaults to name if not provided).
        """
        require_capabilities("circles.enabled", self._session.capabilities)
        params = {"name": name}
        if display_name:
            params["displayName"] = display_name
        clear_from_params_empty(list(params.keys()), params)
        return Circle(self._session.ocs("POST", self._ep_base, json=params))

    def delete(self, circle_id: str) -> None:
        """Deletes a circle.

        :raises NextcloudException: If the circle is managed elsewhere (error code 120).
        """
        require_capabilities("circles.enabled", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._ep_base}/{circle_id}")
        except NextcloudException as e:
            if e.status_code == 120:
                raise NextcloudException(
                    status_code=120, reason="Circle is managed elsewhere and cannot be deleted"
                ) from e
            raise

    def get_members(self, circle_id: str) -> list[CircleMember]:
        """Returns all members of a circle."""
        require_capabilities("circles.enabled", self._session.capabilities)
        result = self._session.ocs("GET", f"{self._ep_base}/{circle_id}/members")
        return [CircleMember(i) for i in result]

    def add_member(self, circle_id: str, member_id: str, member_type: int = 1) -> CircleMember:
        """Adds a member to a circle.

        :param circle_id: ID of the circle.
        :param member_id: ID of the member to add.
        :param member_type: Type of member (1 = User, 2 = Group, 3 = Circle).
        """
        require_capabilities("circles.enabled", self._session.capabilities)
        params = {"id": member_id, "type": member_type}
        result = self._session.ocs("POST", f"{self._ep_base}/{circle_id}/members", json=params)
        return CircleMember(result)

    def bulk_add_members(self, circle_id: str, members: list[dict]) -> list[CircleMember]:
        """Adds multiple members to a circle at once.

        :param circle_id: ID of the circle.
        :param members: List of member dictionaries, each containing 'id' and 'type' keys.
        """
        require_capabilities("circles.enabled", self._session.capabilities)
        params = {"members": members}
        result = self._session.ocs("POST", f"{self._ep_base}/{circle_id}/members/multi", json=params)
        return [CircleMember(i) for i in result]

    def remove_member(self, circle_id: str, member_id: str) -> None:
        """Removes a member from a circle."""
        require_capabilities("circles.enabled", self._session.capabilities)
        self._session.ocs("DELETE", f"{self._ep_base}/{circle_id}/members/{member_id}")


class _AsyncCirclesAPI:
    """Class provides async Circles API on the Nextcloud server."""

    _ep_base: str = "/ocs/v2.php/apps/circles/circles"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("circles.enabled", await self._session.capabilities)

    async def get_list(self) -> list[Circle]:
        """Returns a list of all circles accessible to the current user."""
        require_capabilities("circles.enabled", await self._session.capabilities)
        result = await self._session.ocs("GET", self._ep_base)
        return [Circle(i) for i in result]

    async def get(self, circle_id: str) -> Circle:
        """Returns a specific circle by ID."""
        require_capabilities("circles.enabled", await self._session.capabilities)
        return Circle(await self._session.ocs("GET", f"{self._ep_base}/{circle_id}"))

    async def create(self, name: str, display_name: str = "") -> Circle:
        """Creates a new circle.

        :param name: Name of the circle.
        :param display_name: Display name of the circle (defaults to name if not provided).
        """
        require_capabilities("circles.enabled", await self._session.capabilities)
        params = {"name": name}
        if display_name:
            params["displayName"] = display_name
        clear_from_params_empty(list(params.keys()), params)
        return Circle(await self._session.ocs("POST", self._ep_base, json=params))

    async def delete(self, circle_id: str) -> None:
        """Deletes a circle.

        :raises NextcloudException: If the circle is managed elsewhere (error code 120).
        """
        require_capabilities("circles.enabled", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._ep_base}/{circle_id}")
        except NextcloudException as e:
            if e.status_code == 120:
                raise NextcloudException(
                    status_code=120, reason="Circle is managed elsewhere and cannot be deleted"
                ) from e
            raise

    async def get_members(self, circle_id: str) -> list[CircleMember]:
        """Returns all members of a circle."""
        require_capabilities("circles.enabled", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/{circle_id}/members")
        return [CircleMember(i) for i in result]

    async def add_member(self, circle_id: str, member_id: str, member_type: int = 1) -> CircleMember:
        """Adds a member to a circle.

        :param circle_id: ID of the circle.
        :param member_id: ID of the member to add.
        :param member_type: Type of member (1 = User, 2 = Group, 3 = Circle).
        """
        require_capabilities("circles.enabled", await self._session.capabilities)
        params = {"id": member_id, "type": member_type}
        result = await self._session.ocs("POST", f"{self._ep_base}/{circle_id}/members", json=params)
        return CircleMember(result)

    async def bulk_add_members(self, circle_id: str, members: list[dict]) -> list[CircleMember]:
        """Adds multiple members to a circle at once.

        :param circle_id: ID of the circle.
        :param members: List of member dictionaries, each containing 'id' and 'type' keys.
        """
        require_capabilities("circles.enabled", await self._session.capabilities)
        params = {"members": members}
        result = await self._session.ocs("POST", f"{self._ep_base}/{circle_id}/members/multi", json=params)
        return [CircleMember(i) for i in result]

    async def remove_member(self, circle_id: str, member_id: str) -> None:
        """Removes a member from a circle."""
        require_capabilities("circles.enabled", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/{circle_id}/members/{member_id}")
