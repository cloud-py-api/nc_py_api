"""Definitions related to Users, Groups, Notifications, User Statuses and Weather Status."""

from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from enum import IntEnum
from typing import Optional, Union


@dataclass
class GroupDetails:
    """User Group information"""

    group_id: str
    """ID of the group"""
    display_name: str
    """Display name of the group"""
    user_count: int
    """Number of users in the group"""
    disabled: bool
    """Flag indicating is group disabled"""
    can_add: bool
    """Flag showing the caller has enough rights to add users to this group"""
    can_remove: bool
    """Flag showing the caller has enough rights to remove users from this group"""

    def __init__(self, raw_group: dict):
        self.group_id = raw_group["id"]
        self.display_name = raw_group["displayname"]
        self.user_count = raw_group["usercount"]
        self.disabled = bool(raw_group["disabled"])
        self.can_add = bool(raw_group["canAdd"])
        self.can_remove = bool(raw_group["canRemove"])


@dataclass
class ClearAt:
    """Determination when a user's predefined status will be cleared."""

    clear_type: str
    """Possible values: ``period``, ``end-of``"""
    time: Union[str, int]
    """Depending of ``type`` it can be number of seconds relative to ``now`` or one of the next values: ``day``"""

    def __init__(self, raw_data: dict):
        self.clear_type = raw_data["type"]
        self.time = raw_data["time"]


@dataclass
class PredefinedStatus:
    """Definition of the predefined status."""

    status_id: str
    """ID of the predefined status"""
    icon: str
    """Icon in string(UTF) format"""
    message: str
    """The message defined for this status. It is translated, so it depends on the user's language setting."""
    clear_at: Optional[ClearAt]
    """When the default, if not override, the predefined status will be cleared."""

    def __init__(self, raw_status: dict):
        self.status_id = raw_status["id"]
        self.icon = raw_status["icon"]
        self.message = raw_status["message"]
        clear_at_raw = raw_status.get("clearAt", None)
        if clear_at_raw:
            self.clear_at = ClearAt(clear_at_raw)
        else:
            self.clear_at = None


@dataclass
class UserStatus:
    """Information about user status."""

    user_id: str
    """The ID of the user this status is for"""
    message: str
    """Message of the status"""
    icon: Optional[str]
    """The icon picked by the user (must be one emoji)"""
    clear_at: Optional[int]
    """Unix Timestamp representing the time to clear the status."""
    status_type: str
    """Status type, on of the: online, away, dnd, invisible, offline"""

    def __init__(self, raw_status: dict):
        self.user_id = raw_status["userId"]
        self.message = raw_status["message"]
        self.icon = raw_status["icon"]
        self.clear_at = raw_status["clearAt"]
        self.status_type = raw_status["status"]


@dataclass
class CurrentUserStatus(UserStatus):
    """Information about current user status."""

    status_id: Optional[str]
    """ID of the predefined status"""
    predefined: bool
    """*True* if status if predefined, *False* otherwise"""
    status_type_defined: bool
    """*True* if :py:attr:`UserStatus.status_type` is set by user, *False* otherwise"""

    def __init__(self, raw_status: dict):
        super().__init__(raw_status)
        self.status_id = raw_status["messageId"]
        self.predefined = raw_status["messageIsPredefined"]
        self.status_type_defined = raw_status["statusIsUserDefined"]


class WeatherLocationMode(IntEnum):
    """Source from where Nextcloud should determine user's location."""

    UNKNOWN = 0
    """Source is not defined"""
    MODE_BROWSER_LOCATION = 1
    """User location taken from the browser"""
    MODE_MANUAL_LOCATION = 2
    """User has set their location manually"""


@dataclass
class WeatherLocation:
    latitude: float
    """Latitude in decimal degree format"""
    longitude: float
    """Longitude in decimal degree format"""
    address: str
    """Any approximate or exact address"""
    mode: WeatherLocationMode
    """Weather status mode"""

    def __init__(self, raw_location: dict):
        lat = raw_location.get("lat", "")
        lon = raw_location.get("lon", "")
        self.latitude = float(lat if lat else "0")
        self.longitude = float(lon if lon else "0")
        self.address = raw_location.get("address", "")
        self.mode = WeatherLocationMode(int(raw_location.get("mode", 0)))


@dataclass
class NotificationInfo:
    """Extra Notification attributes from Nextcloud"""

    app_name: str
    """Application name that generated notification."""
    user_id: str
    """User name for which this notification is."""
    time: datetime
    """Time when the notification was created."""
    subject: str
    """Subject of the notification."""
    message: str
    """Message of the notification."""
    link: str
    """Link which will be opened when user clicks on notification."""
    icon: str
    """Relative to instance url of the icon image."""

    def __init__(self, raw_info: dict):
        self.app_name = raw_info["app"]
        self.user_id = raw_info["user"]
        try:
            self.time = parsedate_to_datetime(raw_info["datetime"])
        except (ValueError, TypeError):
            self.time = datetime(1970, 1, 1)
        self.subject = raw_info["subject"]
        self.message = raw_info["message"]
        self.link = raw_info.get("link", "")
        self.icon = raw_info.get("icon", "")


@dataclass
class Notification:
    """A class that represents a Nextcloud Notification."""

    notification_id: int
    """ID of the notification."""
    object_id: str
    """Randomly generated unique object ID"""
    object_type: str
    """Currently not used."""
    info: NotificationInfo
    """Additional extra information for the object"""

    def __init__(self, raw_info: dict):
        self.notification_id = raw_info["notification_id"]
        self.object_id = raw_info["object_id"]
        self.object_type = raw_info["object_type"]
        self.info = NotificationInfo(raw_info)
