"""Nextcloud API for working with users."""

import dataclasses
import datetime
import typing

from ._exceptions import check_error
from ._misc import kwargs_to_params
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class UserInfo:
    """User information description."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def enabled(self) -> bool:
        """Flag indicating whether the user is enabled."""
        return self._raw_data.get("enabled", True)

    @property
    def storage_location(self) -> str:
        """User's home folder. Can be empty for LDAP or when the caller does not have administrative rights."""
        return self._raw_data.get("storageLocation", "")

    @property
    def user_id(self) -> str:
        """User ID."""
        return self._raw_data["id"]

    @property
    def last_login(self) -> datetime.datetime:
        """Last user login time."""
        return datetime.datetime.utcfromtimestamp(int(self._raw_data["lastLogin"] / 1000)).replace(
            tzinfo=datetime.timezone.utc
        )

    @property
    def backend(self) -> str:
        """The type of backend in which user information is stored."""
        return self._raw_data["backend"]

    @property
    def subadmin(self) -> list[str]:
        """IDs of groups of which the user is a subadmin."""
        return self._raw_data.get("subadmin", [])

    @property
    def quota(self) -> dict:
        """Quota for the user, if set."""
        return self._raw_data["quota"] if isinstance(self._raw_data["quota"], dict) else {}

    @property
    def manager(self) -> str:
        """The user's manager UID."""
        return self._raw_data.get("manager", "")

    @property
    def email(self) -> str:
        """Email address of the user."""
        return self._raw_data["email"] if self._raw_data["email"] is not None else ""

    @property
    def additional_mail(self) -> list[str]:
        """List of additional emails."""
        return self._raw_data["additional_mail"]

    @property
    def display_name(self) -> str:
        """The display name of the new user."""
        return self._raw_data["displayname"] if "displayname" in self._raw_data else self._raw_data["display-name"]

    @property
    def phone(self) -> str:
        """Phone of the user."""
        return self._raw_data["phone"]

    @property
    def address(self) -> str:
        """Address of the user."""
        return self._raw_data["address"]

    @property
    def website(self) -> str:
        """Link to user website."""
        return self._raw_data["website"]

    @property
    def twitter(self) -> str:
        """Twitter handle."""
        return self._raw_data["twitter"]

    @property
    def fediverse(self) -> str:
        """Fediverse(e.g. Mastodon) in the user profile."""
        return self._raw_data["fediverse"]

    @property
    def organisation(self) -> str:
        """Organisation in the user profile."""
        return self._raw_data["organisation"]

    @property
    def role(self) -> str:
        """Role in the user profile."""
        return self._raw_data["role"]

    @property
    def headline(self) -> str:
        """Headline in the user profile."""
        return self._raw_data["headline"]

    @property
    def biography(self) -> str:
        """Biography in the user profile."""
        return self._raw_data["biography"]

    @property
    def profile_enabled(self) -> bool:
        """Flag indicating whether the user profile is enabled."""
        return str(self._raw_data["profile_enabled"]).lower() in ("1", "true")

    @property
    def groups(self) -> list[str]:
        """ID of the groups the user is a member of."""
        return self._raw_data["groups"]

    @property
    def language(self) -> str:
        """The language to use when sending something to a user."""
        return self._raw_data["language"]

    @property
    def locale(self) -> str:
        """The locale set for the user."""
        return self._raw_data.get("locale", "")

    @property
    def notify_email(self) -> str:
        """The user's preferred email address.

        .. note:: The primary mail address may be set be the user to specify a different
            email address where mails by Nextcloud are sent to. It is not necessarily set.
        """
        return self._raw_data["notify_email"] if self._raw_data["notify_email"] is not None else ""

    @property
    def backend_capabilities(self) -> dict:
        """By default, only the ``setDisplayName`` and ``setPassword`` keys are available."""
        return self._raw_data["backendCapabilities"]

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.user_id}, backend={self.backend}, last_login={self.last_login}>"


class _UsersAPI:
    """The class provides the user API on the Nextcloud server.

    .. note:: In NextcloudApp mode, only ``get_list``, ``editable_fields`` and ``get_user`` methods are available.
    """

    _ep_base: str = "/ocs/v1.php/cloud/users"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_list(self, mask: str | None = "", limit: int | None = None, offset: int | None = None) -> list[str]:
        """Returns list of user IDs."""
        data = kwargs_to_params(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs("GET", self._ep_base, params=data)
        return response_data["users"] if response_data else {}

    def get_user(self, user_id: str = "") -> UserInfo:
        """Returns detailed user information."""
        return UserInfo(self._session.ocs("GET", f"{self._ep_base}/{user_id}" if user_id else "/ocs/v1.php/cloud/user"))

    def create(self, user_id: str, display_name: str | None = None, **kwargs) -> None:
        """Create a new user on the Nextcloud server.

        :param user_id: id of the user to create.
        :param display_name: display name for a created user.
        :param kwargs: See below.

        Additionally supported arguments:

            * ``password`` - password that should be set for user.
            * ``email`` - email of the new user. If ``password`` is not provided, then this field should be filled.
            * ``groups`` - list of groups IDs to which user belongs.
            * ``subadmin`` - boolean indicating is user should be the subadmin.
            * ``quota`` - quota for the user, if needed.
            * ``language`` - default language for the user.
        """
        self._session.ocs("POST", self._ep_base, json=_create(user_id, display_name, **kwargs))

    def delete(self, user_id: str) -> None:
        """Deletes user from the Nextcloud server."""
        self._session.ocs("DELETE", f"{self._ep_base}/{user_id}")

    def enable(self, user_id: str) -> None:
        """Enables user on the Nextcloud server."""
        self._session.ocs("PUT", f"{self._ep_base}/{user_id}/enable")

    def disable(self, user_id: str) -> None:
        """Disables user on the Nextcloud server."""
        self._session.ocs("PUT", f"{self._ep_base}/{user_id}/disable")

    def resend_welcome_email(self, user_id: str) -> None:
        """Send welcome email for specified user again."""
        self._session.ocs("POST", f"{self._ep_base}/{user_id}/welcome")

    def editable_fields(self) -> list[str]:
        """Returns user fields that avalaible for edit."""
        return self._session.ocs("GET", "/ocs/v1.php/cloud/user/fields")

    def edit(self, user_id: str, **kwargs) -> None:
        """Edits user metadata.

        :param user_id: id of the user.
        :param kwargs: dictionary where keys are values from ``editable_fields`` method, and values to set.
        """
        for k, v in kwargs.items():
            self._session.ocs("PUT", f"{self._ep_base}/{user_id}", params={"key": k, "value": v})

    def add_to_group(self, user_id: str, group_id: str) -> None:
        """Adds user to the group."""
        self._session.ocs("POST", f"{self._ep_base}/{user_id}/groups", params={"groupid": group_id})

    def remove_from_group(self, user_id: str, group_id: str) -> None:
        """Removes user from the group."""
        self._session.ocs("DELETE", f"{self._ep_base}/{user_id}/groups", params={"groupid": group_id})

    def promote_to_subadmin(self, user_id: str, group_id: str) -> None:
        """Makes user admin of the group."""
        self._session.ocs("POST", f"{self._ep_base}/{user_id}/subadmins", params={"groupid": group_id})

    def demote_from_subadmin(self, user_id: str, group_id: str) -> None:
        """Removes user from the admin role of the group."""
        self._session.ocs("DELETE", f"{self._ep_base}/{user_id}/subadmins", params={"groupid": group_id})

    def get_avatar(
        self, user_id: str = "", size: typing.Literal[64, 512] = 512, dark: bool = False, guest: bool = False
    ) -> bytes:
        """Returns user avatar binary data.

        :param user_id: The ID of the user whose avatar should be returned.
            .. note:: To return the current user's avatar, leave the field blank.
        :param size: Size of the avatar. Currently supported values: ``64`` and ``512``.
        :param dark: Flag indicating whether a dark theme avatar should be returned or not.
        :param guest: Flag indicating whether user ID is a guest name or not.
        """
        if not user_id and not guest:
            user_id = self._session.user
        url_path = f"/index.php/avatar/{user_id}/{size}" if not guest else f"/index.php/avatar/guest/{user_id}/{size}"
        if dark:
            url_path += "/dark"
        response = self._session.adapter.get(url_path)
        check_error(response)
        return response.content


class _AsyncUsersAPI:
    """The class provides the async user API on the Nextcloud server.

    .. note:: In NextcloudApp mode, only ``get_list``, ``editable_fields`` and ``get_user`` methods are available.
    """

    _ep_base: str = "/ocs/v1.php/cloud/users"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    async def get_list(self, mask: str | None = "", limit: int | None = None, offset: int | None = None) -> list[str]:
        """Returns list of user IDs."""
        data = kwargs_to_params(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = await self._session.ocs("GET", self._ep_base, params=data)
        return response_data["users"] if response_data else {}

    async def get_user(self, user_id: str = "") -> UserInfo:
        """Returns detailed user information."""
        return UserInfo(
            await self._session.ocs("GET", f"{self._ep_base}/{user_id}" if user_id else "/ocs/v1.php/cloud/user")
        )

    async def create(self, user_id: str, display_name: str | None = None, **kwargs) -> None:
        """Create a new user on the Nextcloud server.

        :param user_id: id of the user to create.
        :param display_name: display name for a created user.
        :param kwargs: See below.

        Additionally supported arguments:

            * ``password`` - password that should be set for user.
            * ``email`` - email of the new user. If ``password`` is not provided, then this field should be filled.
            * ``groups`` - list of groups IDs to which user belongs.
            * ``subadmin`` - boolean indicating is user should be the subadmin.
            * ``quota`` - quota for the user, if needed.
            * ``language`` - default language for the user.
        """
        await self._session.ocs("POST", self._ep_base, json=_create(user_id, display_name, **kwargs))

    async def delete(self, user_id: str) -> None:
        """Deletes user from the Nextcloud server."""
        await self._session.ocs("DELETE", f"{self._ep_base}/{user_id}")

    async def enable(self, user_id: str) -> None:
        """Enables user on the Nextcloud server."""
        await self._session.ocs("PUT", f"{self._ep_base}/{user_id}/enable")

    async def disable(self, user_id: str) -> None:
        """Disables user on the Nextcloud server."""
        await self._session.ocs("PUT", f"{self._ep_base}/{user_id}/disable")

    async def resend_welcome_email(self, user_id: str) -> None:
        """Send welcome email for specified user again."""
        await self._session.ocs("POST", f"{self._ep_base}/{user_id}/welcome")

    async def editable_fields(self) -> list[str]:
        """Returns user fields that avalaible for edit."""
        return await self._session.ocs("GET", "/ocs/v1.php/cloud/user/fields")

    async def edit(self, user_id: str, **kwargs) -> None:
        """Edits user metadata.

        :param user_id: id of the user.
        :param kwargs: dictionary where keys are values from ``editable_fields`` method, and values to set.
        """
        for k, v in kwargs.items():
            await self._session.ocs("PUT", f"{self._ep_base}/{user_id}", params={"key": k, "value": v})

    async def add_to_group(self, user_id: str, group_id: str) -> None:
        """Adds user to the group."""
        await self._session.ocs("POST", f"{self._ep_base}/{user_id}/groups", params={"groupid": group_id})

    async def remove_from_group(self, user_id: str, group_id: str) -> None:
        """Removes user from the group."""
        await self._session.ocs("DELETE", f"{self._ep_base}/{user_id}/groups", params={"groupid": group_id})

    async def promote_to_subadmin(self, user_id: str, group_id: str) -> None:
        """Makes user admin of the group."""
        await self._session.ocs("POST", f"{self._ep_base}/{user_id}/subadmins", params={"groupid": group_id})

    async def demote_from_subadmin(self, user_id: str, group_id: str) -> None:
        """Removes user from the admin role of the group."""
        await self._session.ocs("DELETE", f"{self._ep_base}/{user_id}/subadmins", params={"groupid": group_id})

    async def get_avatar(
        self, user_id: str = "", size: typing.Literal[64, 512] = 512, dark: bool = False, guest: bool = False
    ) -> bytes:
        """Returns user avatar binary data.

        :param user_id: The ID of the user whose avatar should be returned.
            .. note:: To return the current user's avatar, leave the field blank.
        :param size: Size of the avatar. Currently supported values: ``64`` and ``512``.
        :param dark: Flag indicating whether a dark theme avatar should be returned or not.
        :param guest: Flag indicating whether user ID is a guest name or not.
        """
        if not user_id and not guest:
            user_id = await self._session.user
        url_path = f"/index.php/avatar/{user_id}/{size}" if not guest else f"/index.php/avatar/guest/{user_id}/{size}"
        if dark:
            url_path += "/dark"
        response = await self._session.adapter.get(url_path)
        check_error(response)
        return response.content


def _create(user_id: str, display_name: str | None, **kwargs) -> dict[str, typing.Any]:
    password = kwargs.get("password", None)
    email = kwargs.get("email", None)
    if not password and not email:
        raise ValueError("Either password or email must be set")
    data = {"userid": user_id}
    for k in ("password", "email", "groups", "subadmin", "quota", "language"):
        if k in kwargs:
            data[k] = kwargs[k]
    if display_name is not None:
        data["displayName"] = display_name
    return data
