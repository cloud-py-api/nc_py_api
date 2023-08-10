"""Nextcloud API for working with Notifications."""

from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

from .._misc import check_capabilities, random_string, require_capabilities
from .._session import NcSessionApp, NcSessionBasic


@dataclass
class NotificationInfo:
    """Extra Notification attributes from Nextcloud."""

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
    """Class representing information about Nextcloud notification."""

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


class _NotificationsAPI:
    """Class providing an API for managing user notifications on the Nextcloud server."""

    _ep_base: str = "/ocs/v2.php/apps/notifications/api/v2/notifications"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("notifications", self._session.capabilities)

    def create(
        self,
        subject: str,
        message: str = "",
        subject_params: Optional[dict] = None,
        message_params: Optional[dict] = None,
        link: str = "",
    ) -> str:
        """Create a Notification for the current user and returns it's ObjectID.

        .. note:: Does not work in Nextcloud client mode, only for NextcloudApp mode.
        """
        if not isinstance(self._session, NcSessionApp):
            raise NotImplementedError("Sending notifications is only supported for `App` mode.")
        if not subject:
            raise ValueError("`subject` cannot be empty string.")
        require_capabilities(["app_ecosystem_v2", "notifications"], self._session.capabilities)
        if subject_params is None:
            subject_params = {}
        if message_params is None:
            message_params = {}
        params: dict = {
            "params": {
                "object": "app_ecosystem_v2",
                "object_id": random_string(56),
                "subject_type": "app_ecosystem_v2_ex_app",
                "subject_params": {
                    "rich_subject": subject,
                    "rich_subject_params": subject_params,
                    "rich_message": message,
                    "rich_message_params": message_params,
                },
            }
        }
        if link:
            params["params"]["subject_params"]["link"] = link
        return self._session.ocs(method="POST", path=f"{self._session.ae_url}/notification", json=params)["object_id"]

    def get_all(self) -> list[Notification]:
        """Gets all notifications for a current user."""
        require_capabilities("notifications", self._session.capabilities)
        return [Notification(i) for i in self._session.ocs(method="GET", path=self._ep_base)]

    def get_one(self, notification_id: int) -> Notification:
        """Gets a single notification for a current user."""
        require_capabilities("notifications", self._session.capabilities)
        return Notification(self._session.ocs(method="GET", path=f"{self._ep_base}/{notification_id}"))

    def by_object_id(self, object_id: str) -> Optional[Notification]:
        """Returns Notification if any by its object ID.

        .. note:: this method is a temporary workaround until `create` can return `notification_id`.
        """
        for i in self.get_all():
            if i.object_id == object_id:
                return i
        return None

    def delete(self, notification_id: int) -> None:
        """Deletes a notification for the current user."""
        require_capabilities("notifications", self._session.capabilities)
        self._session.ocs(method="DELETE", path=f"{self._ep_base}/{notification_id}")

    def delete_all(self) -> None:
        """Deletes all notifications for the current user."""
        require_capabilities("notifications", self._session.capabilities)
        self._session.ocs(method="DELETE", path=self._ep_base)

    def exists(self, notification_ids: list[int]) -> list[int]:
        """Checks the existence of notifications for the current user."""
        require_capabilities("notifications", self._session.capabilities)
        return self._session.ocs(method="POST", path=f"{self._ep_base}/exists", json={"ids": notification_ids})
