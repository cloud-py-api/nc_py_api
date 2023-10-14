"""Nextcloud API for working with Notifications."""

import dataclasses
import datetime
import typing

from ._misc import (
    check_capabilities,
    nc_iso_time_to_datetime,
    random_string,
    require_capabilities,
)
from ._session import NcSessionApp, NcSessionBasic


@dataclasses.dataclass
class Notification:
    """Class representing information about Nextcloud notification."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def notification_id(self) -> int:
        """ID of the notification."""
        return self._raw_data["notification_id"]

    @property
    def object_id(self) -> str:
        """Randomly generated unique object ID."""
        return self._raw_data["object_id"]

    @property
    def object_type(self) -> str:
        """Currently not used."""
        return self._raw_data["object_type"]

    @property
    def app_name(self) -> str:
        """Application name that generated notification."""
        return self._raw_data["app"]

    @property
    def user_id(self) -> str:
        """User ID of user for which this notification is."""
        return self._raw_data["user"]

    @property
    def subject(self) -> str:
        """Subject of the notification."""
        return self._raw_data["subject"]

    @property
    def message(self) -> str:
        """Message of the notification."""
        return self._raw_data["message"]

    @property
    def time(self) -> datetime.datetime:
        """Time when the notification was created."""
        return nc_iso_time_to_datetime(self._raw_data["datetime"])

    @property
    def link(self) -> str:
        """Link, which will be opened when user clicks on notification."""
        return self._raw_data.get("link", "")

    @property
    def icon(self) -> str:
        """Relative to instance url of the icon image."""
        return self._raw_data.get("icon", "")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} id={self.notification_id}, app_name={self.app_name}, user_id={self.user_id},"
            f" time={self.time}>"
        )


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
        subject_params: typing.Optional[dict] = None,
        message_params: typing.Optional[dict] = None,
        link: str = "",
    ) -> str:
        """Create a Notification for the current user and returns it's ObjectID.

        .. note:: Does not work in Nextcloud client mode, only for NextcloudApp mode.
        """
        if not isinstance(self._session, NcSessionApp):
            raise NotImplementedError("Sending notifications is only supported for `App` mode.")
        if not subject:
            raise ValueError("`subject` cannot be empty string.")
        require_capabilities(["app_api", "notifications"], self._session.capabilities)
        if subject_params is None:
            subject_params = {}
        if message_params is None:
            message_params = {}
        params: dict = {
            "params": {
                "object": "app_api",
                "object_id": random_string(56),
                "subject_type": "app_api_ex_app",
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

    def by_object_id(self, object_id: str) -> typing.Optional[Notification]:
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
