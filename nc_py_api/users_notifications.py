"""Nextcloud API for working with Notifications."""


from typing import Optional

from ._session import NcSessionApp, NcSessionBasic
from .constants import APP_V2_BASIC_URL
from .misc import check_capabilities, random_string, require_capabilities
from .users_defs import Notification

ENDPOINT = "/ocs/v2.php/apps/notifications/api/v2/notifications"


class NotificationsAPI:
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
        """Create a Notification for the current user and returns it's ObjectID."""
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
        return self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/notification", json=params)["object_id"]

    def get_all(self) -> list[Notification]:
        """Gets all notifications for a current user."""
        require_capabilities("notifications", self._session.capabilities)
        return [Notification(i) for i in self._session.ocs(method="GET", path=ENDPOINT)]

    def get_one(self, notification_id: int) -> Notification:
        """Gets a single notification for a current user."""
        require_capabilities("notifications", self._session.capabilities)
        return Notification(self._session.ocs(method="GET", path=f"{ENDPOINT}/{notification_id}"))

    def by_object_id(self, object_id: str) -> Optional[Notification]:
        """Returns Notification if any by its object ID.

        .. note:: this method is a temporary workaround until `create` can return `notification_id`."""
        for i in self.get_all():
            if i.object_id == object_id:
                return i
        return None

    def delete(self, notification_id: int) -> None:
        """Deletes a notification for the current user."""
        require_capabilities("notifications", self._session.capabilities)
        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{notification_id}")

    def delete_all(self) -> None:
        """Deletes all notifications for the current user."""
        require_capabilities("notifications", self._session.capabilities)
        self._session.ocs(method="DELETE", path=ENDPOINT)

    def exists(self, notification_ids: list[int]) -> list[int]:
        """Checks the existence of notifications for the current user."""
        require_capabilities("notifications", self._session.capabilities)
        return self._session.ocs(method="POST", path=f"{ENDPOINT}/exists", json={"ids": notification_ids})
