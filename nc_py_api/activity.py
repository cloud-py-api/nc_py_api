"""API for working with Activity App."""

import dataclasses
import datetime
import typing

from ._exceptions import NextcloudExceptionNotModified
from ._misc import check_capabilities, nc_iso_time_to_datetime
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class ActivityFilter:
    """Activity filter description."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def icon(self) -> str:
        """Icon for filter."""
        return self._raw_data["icon"]

    @property
    def filter_id(self) -> str:
        """Filter ID."""
        return self._raw_data["id"]

    @property
    def name(self) -> str:
        """Filter name."""
        return self._raw_data["name"]

    @property
    def priority(self) -> int:
        """Arrangement priority in ascending order. Values from 0 to 99."""
        return self._raw_data["priority"]

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.filter_id}, name={self.name}, priority={self.priority}>"


@dataclasses.dataclass
class Activity:
    """Description of one activity."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def activity_id(self) -> int:
        """Unique for one Nextcloud instance activity ID."""
        return self._raw_data["activity_id"]

    @property
    def app(self) -> str:
        """App that created the activity (e.g. 'files', 'files_sharing', etc.)."""
        return self._raw_data["app"]

    @property
    def activity_type(self) -> str:
        """String describing the activity type, depends on the **app** field."""
        return self._raw_data["type"]

    @property
    def actor_id(self) -> str:
        """User ID of the user that triggered/created this activity.

        .. note:: Can be empty in case of public link/remote share action.
        """
        return self._raw_data["user"]

    @property
    def subject(self) -> str:
        """Translated simple subject without markup, ready for use (e.g. 'You created hello.jpg')."""
        return self._raw_data["subject"]

    @property
    def subject_rich(self) -> list:
        """`0` is the string subject including placeholders, `1` is an array with the placeholders."""
        return self._raw_data["subject_rich"]

    @property
    def message(self) -> str:
        """Translated message without markup, ready for use (longer text, unused by core apps)."""
        return self._raw_data["message"]

    @property
    def message_rich(self) -> list:
        """See description of **subject_rich**."""
        return self._raw_data["message_rich"]

    @property
    def object_type(self) -> str:
        """The Type of the object this activity is about (e.g. 'files' is used for files and folders)."""
        return self._raw_data["object_type"]

    @property
    def object_id(self) -> int:
        """ID of the object this activity is about (e.g., ID in the file cache is used for files and folders)."""
        return self._raw_data["object_id"]

    @property
    def object_name(self) -> str:
        """The name of the object this activity is about (e.g., for files it's the relative path to the user's root)."""
        return self._raw_data["object_name"]

    @property
    def objects(self) -> dict:
        """Contains the objects involved in multi-object activities, like editing multiple files in a folder.

        .. note:: They are stored in objects as key-value pairs of the object_id and the object_name:
            { object_id: object_name}
        """
        return self._raw_data["objects"] if isinstance(self._raw_data["objects"], dict) else {}

    @property
    def link(self) -> str:
        """A full URL pointing to a suitable location (e.g. 'http://localhost/apps/files/?dir=%2Ffolder' for folder)."""
        return self._raw_data["link"]

    @property
    def icon(self) -> str:
        """URL of the icon."""
        return self._raw_data["icon"]

    @property
    def time(self) -> datetime.datetime:
        """Time when the activity occurred."""
        return nc_iso_time_to_datetime(self._raw_data["datetime"])

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} id={self.activity_id}, app={self.app}, type={self.activity_type},"
            f" time={self.time}>"
        )


class _ActivityAPI:
    """The class provides the Activity Application API."""

    _ep_base: str = "/ocs/v1.php/apps/activity"
    last_given: int
    """Used by ``get_activities``, when **since** param is ``True``."""

    def __init__(self, session: NcSessionBasic):
        self._session = session
        self.last_given = 0

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("activity.apiv2", self._session.capabilities)

    def get_activities(
        self,
        filter_id: ActivityFilter | str = "",
        since: int | bool = 0,
        limit: int = 50,
        object_type: str = "",
        object_id: int = 0,
        sort: str = "desc",
    ) -> list[Activity]:
        """Returns activities for the current user.

        :param filter_id: Filter to apply, if needed.
        :param since: Last activity ID you have seen. When specified, only activities after provided are returned.
            Can be set to ``True`` to automatically use last ``last_given`` from previous calls. Default = **0**.
        :param limit: Max number of activities to be returned.
        :param object_type: Filter the activities to a given object.
        :param object_id: Filter the activities to a given object.
        :param sort: Sort activities ascending or descending. Default is ``desc``.

        .. note:: ``object_type`` and ``object_id`` should only appear together with ``filter_id`` unset.
        """
        if since is True:
            since = self.last_given
        url, params = _get_activities(filter_id, since, limit, object_type, object_id, sort)
        try:
            result = self._session.ocs("GET", self._ep_base + url, params=params)
        except NextcloudExceptionNotModified:
            return []
        self.last_given = int(self._session.response_headers["X-Activity-Last-Given"])
        return [Activity(i) for i in result]

    def get_filters(self) -> list[ActivityFilter]:
        """Returns avalaible activity filters."""
        return [ActivityFilter(i) for i in self._session.ocs("GET", self._ep_base + "/api/v2/activity/filters")]


class _AsyncActivityAPI:
    """The class provides the async Activity Application API."""

    _ep_base: str = "/ocs/v1.php/apps/activity"
    last_given: int
    """Used by ``get_activities``, when **since** param is ``True``."""

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session
        self.last_given = 0

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("activity.apiv2", await self._session.capabilities)

    async def get_activities(
        self,
        filter_id: ActivityFilter | str = "",
        since: int | bool = 0,
        limit: int = 50,
        object_type: str = "",
        object_id: int = 0,
        sort: str = "desc",
    ) -> list[Activity]:
        """Returns activities for the current user.

        :param filter_id: Filter to apply, if needed.
        :param since: Last activity ID you have seen. When specified, only activities after provided are returned.
            Can be set to ``True`` to automatically use last ``last_given`` from previous calls. Default = **0**.
        :param limit: Max number of activities to be returned.
        :param object_type: Filter the activities to a given object.
        :param object_id: Filter the activities to a given object.
        :param sort: Sort activities ascending or descending. Default is ``desc``.

        .. note:: ``object_type`` and ``object_id`` should only appear together with ``filter_id`` unset.
        """
        if since is True:
            since = self.last_given
        url, params = _get_activities(filter_id, since, limit, object_type, object_id, sort)
        try:
            result = await self._session.ocs("GET", self._ep_base + url, params=params)
        except NextcloudExceptionNotModified:
            return []
        self.last_given = int(self._session.response_headers["X-Activity-Last-Given"])
        return [Activity(i) for i in result]

    async def get_filters(self) -> list[ActivityFilter]:
        """Returns avalaible activity filters."""
        return [ActivityFilter(i) for i in await self._session.ocs("GET", self._ep_base + "/api/v2/activity/filters")]


def _get_activities(
    filter_id: ActivityFilter | str, since: int | bool, limit: int, object_type: str, object_id: int, sort: str
) -> tuple[str, dict[str, typing.Any]]:
    if bool(object_id) != bool(object_type):
        raise ValueError("Either specify both `object_type` and `object_id`, or don't specify any at all.")
    filter_id = filter_id.filter_id if isinstance(filter_id, ActivityFilter) else filter_id
    params = {
        "since": since,
        "limit": limit,
        "object_type": object_type,
        "object_id": object_id,
        "sort": sort,
    }
    url = (
        f"/api/v2/activity/{filter_id}" if filter_id else "/api/v2/activity/filter" if object_id else "/api/v2/activity"
    )
    return url, params
