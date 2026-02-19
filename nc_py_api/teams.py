"""Nextcloud API for working with Teams (Circles)."""

import dataclasses
import enum

from ._misc import check_capabilities, require_capabilities
from ._session import AsyncNcSessionBasic


class MemberType(enum.IntEnum):
    """Type of a Team member."""

    SINGLE = 0
    """Single (personal circle owner)"""
    USER = 1
    """Nextcloud user"""
    GROUP = 2
    """Nextcloud group"""
    MAIL = 4
    """Email address"""
    CONTACT = 8
    """Contact"""
    CIRCLE = 16
    """Another team/circle"""
    APP = 10000
    """Application"""


class MemberLevel(enum.IntEnum):
    """Permission level of a Team member."""

    NONE = 0
    """No level (not a member)"""
    MEMBER = 1
    """Regular member"""
    MODERATOR = 4
    """Moderator"""
    ADMIN = 8
    """Administrator"""
    OWNER = 9
    """Owner"""


class CircleConfig(enum.IntFlag):
    """Configuration flags for a Team (circle). Flags can be combined with bitwise OR."""

    DEFAULT = 0
    """Default: locked circle, only moderator can add members"""
    SINGLE = 1
    """Circle with only one single member"""
    PERSONAL = 2
    """Personal circle, only the owner can see it"""
    SYSTEM = 4
    """System circle (not managed by the official front-end)"""
    VISIBLE = 8
    """Visible to everyone; if not set, people must know its name"""
    OPEN = 16
    """Open circle, anyone can join"""
    INVITE = 32
    """Adding a member generates an invitation that must be accepted"""
    REQUEST = 64
    """Request to join needs moderator confirmation"""
    FRIEND = 128
    """Members can invite their friends"""
    PROTECTED = 256
    """Password protected to join/request"""
    NO_OWNER = 512
    """No owner, only members"""
    HIDDEN = 1024
    """Hidden from listing, but available as share entity"""
    BACKEND = 2048
    """Fully hidden, only backend circles"""
    LOCAL = 4096
    """Local even on GlobalScale"""
    ROOT = 8192
    """Circle cannot be inside another circle"""
    CIRCLE_INVITE = 16384
    """Circle must confirm when invited in another circle"""
    FEDERATED = 32768
    """Federated"""
    MOUNTPOINT = 65536
    """Generate a Files folder for this circle"""
    APP = 131072
    """App-managed: some features unavailable to OCS API"""


@dataclasses.dataclass
class Member:
    """Team member information."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def member_id(self) -> str:
        """Unique ID of the member within the circle."""
        return self._raw_data.get("id", "")

    @property
    def circle_id(self) -> str:
        """ID of the circle this member belongs to."""
        return self._raw_data.get("circleId", "")

    @property
    def single_id(self) -> str:
        """Single ID of the member."""
        return self._raw_data.get("singleId", "")

    @property
    def user_id(self) -> str:
        """User ID of the member."""
        return self._raw_data.get("userId", "")

    @property
    def user_type(self) -> MemberType:
        """Type of the member."""
        return MemberType(self._raw_data.get("userType", 1))

    @property
    def level(self) -> MemberLevel:
        """Permission level of the member."""
        return MemberLevel(self._raw_data.get("level", 0))

    @property
    def status(self) -> str:
        """Status of the member (Member, Invited, Requesting, Blocked)."""
        return self._raw_data.get("status", "")

    @property
    def display_name(self) -> str:
        """Display name of the member."""
        return self._raw_data.get("displayName", "")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} user_id={self.user_id}, level={self.level.name}, status={self.status}>"


@dataclasses.dataclass
class Circle:
    """Team (Circle) information."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def circle_id(self) -> str:
        """Unique ID of the circle."""
        return self._raw_data.get("id", "")

    @property
    def name(self) -> str:
        """Name of the circle."""
        return self._raw_data.get("name", "")

    @property
    def display_name(self) -> str:
        """Display name of the circle."""
        return self._raw_data.get("displayName", "")

    @property
    def sanitized_name(self) -> str:
        """Sanitized name of the circle."""
        return self._raw_data.get("sanitizedName", "")

    @property
    def config(self) -> CircleConfig:
        """Configuration flags for the circle."""
        return CircleConfig(self._raw_data.get("config", 0))

    @property
    def description(self) -> str:
        """Description of the circle."""
        return self._raw_data.get("description", "")

    @property
    def population(self) -> int:
        """Number of members in the circle."""
        return self._raw_data.get("population", 0)

    @property
    def url(self) -> str:
        """URL of the circle."""
        return self._raw_data.get("url", "")

    @property
    def creation(self) -> int:
        """Creation timestamp."""
        return self._raw_data.get("creation", 0)

    @property
    def owner(self) -> Member | None:
        """Owner of the circle."""
        owner_data = self._raw_data.get("owner")
        return Member(owner_data) if owner_data else None

    @property
    def initiator(self) -> Member | None:
        """The requesting user's membership details in this circle."""
        initiator_data = self._raw_data.get("initiator")
        return Member(initiator_data) if initiator_data else None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.circle_id}, name={self.name}, population={self.population}>"


class _AsyncTeamsAPI:
    """Class providing the async API for managing Teams (Circles) on the Nextcloud server."""

    _ep_base: str = "/ocs/v2.php/apps/circles"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports Teams (Circles), False otherwise."""
        return not check_capabilities("circles", await self._session.capabilities)

    async def get_list(self) -> list[Circle]:
        """Returns the list of all circles available to the current user."""
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/circles")
        return [Circle(c) for c in result] if result else []

    async def create(self, name: str, personal: bool = False, local: bool = False) -> Circle:
        """Creates a new circle (team).

        :param name: Name of the new circle.
        :param personal: If True, creates a personal circle visible only to the owner.
        :param local: If True, creates a circle limited to the local instance.
        """
        require_capabilities("circles", await self._session.capabilities)
        params: dict[str, str | int | bool] = {"name": name}
        if personal:
            params["personal"] = True
        if local:
            params["local"] = True
        result = await self._session.ocs("POST", f"{self._ep_base}/circles", params=params)
        return Circle(result)

    async def get_details(self, circle_id: str) -> Circle:
        """Returns detailed information about a circle.

        :param circle_id: ID of the circle.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/circles/{circle_id}")
        return Circle(result)

    async def destroy(self, circle_id: str) -> None:
        """Destroys a circle.

        :param circle_id: ID of the circle to destroy.
        """
        require_capabilities("circles", await self._session.capabilities)
        await self._session.ocs("DELETE", f"{self._ep_base}/circles/{circle_id}")

    async def edit_name(self, circle_id: str, name: str) -> Circle:
        """Changes the name of a circle.

        :param circle_id: ID of the circle.
        :param name: New name for the circle.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs(
            "PUT", f"{self._ep_base}/circles/{circle_id}/name", params={"value": name}
        )
        return Circle(result)

    async def edit_description(self, circle_id: str, description: str) -> Circle:
        """Changes the description of a circle.

        :param circle_id: ID of the circle.
        :param description: New description for the circle.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs(
            "PUT", f"{self._ep_base}/circles/{circle_id}/description", params={"value": description}
        )
        return Circle(result)

    async def edit_config(self, circle_id: str, config: int) -> Circle:
        """Changes the configuration flags of a circle.

        :param circle_id: ID of the circle.
        :param config: New configuration bitmask (combination of CircleConfig flags).
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs(
            "PUT", f"{self._ep_base}/circles/{circle_id}/config", params={"value": config}
        )
        return Circle(result)

    async def get_members(self, circle_id: str) -> list[Member]:
        """Returns the list of members in a circle.

        :param circle_id: ID of the circle.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs("GET", f"{self._ep_base}/circles/{circle_id}/members")
        return [Member(m) for m in result] if result else []

    async def add_member(
        self, circle_id: str, user_id: str, member_type: MemberType = MemberType.USER
    ) -> list[Member]:
        """Adds a single member to a circle.

        :param circle_id: ID of the circle.
        :param user_id: ID of the user to add.
        :param member_type: Type of the member to add.
        """
        require_capabilities("circles", await self._session.capabilities)
        params: dict[str, str | int] = {"userId": user_id, "type": int(member_type)}
        result = await self._session.ocs("POST", f"{self._ep_base}/circles/{circle_id}/members", params=params)
        return [Member(m) for m in result] if result else []

    async def add_members(self, circle_id: str, members: list[dict[str, str | int]]) -> list[Member]:
        """Adds multiple members to a circle at once.

        :param circle_id: ID of the circle.
        :param members: List of dicts with ``id`` and ``type`` keys.
            Example: ``[{"id": "user1", "type": 1}, {"id": "user2", "type": 1}]``
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs(
            "POST", f"{self._ep_base}/circles/{circle_id}/members/multi", json={"members": members}
        )
        return [Member(m) for m in result] if result else []

    async def remove_member(self, circle_id: str, member_id: str) -> list[Member]:
        """Removes a member from a circle.

        :param circle_id: ID of the circle.
        :param member_id: ID of the member to remove.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs(
            "DELETE", f"{self._ep_base}/circles/{circle_id}/members/{member_id}"
        )
        return [Member(m) for m in result] if result else []

    async def set_member_level(self, circle_id: str, member_id: str, level: MemberLevel) -> Member:
        """Changes the permission level of a member.

        :param circle_id: ID of the circle.
        :param member_id: ID of the member.
        :param level: New permission level for the member.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs(
            "PUT",
            f"{self._ep_base}/circles/{circle_id}/members/{member_id}/level",
            json={"level": int(level)},
        )
        return Member(result)

    async def confirm_member(self, circle_id: str, member_id: str) -> list[Member]:
        """Confirms a pending member request.

        :param circle_id: ID of the circle.
        :param member_id: ID of the member to confirm.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs(
            "PUT", f"{self._ep_base}/circles/{circle_id}/members/{member_id}"
        )
        return [Member(m) for m in result] if result else []

    async def join(self, circle_id: str) -> Circle:
        """Joins an open circle.

        :param circle_id: ID of the circle to join.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs("PUT", f"{self._ep_base}/circles/{circle_id}/join")
        return Circle(result)

    async def leave(self, circle_id: str) -> Circle:
        """Leaves a circle.

        :param circle_id: ID of the circle to leave.
        """
        require_capabilities("circles", await self._session.capabilities)
        result = await self._session.ocs("PUT", f"{self._ep_base}/circles/{circle_id}/leave")
        return Circle(result)
