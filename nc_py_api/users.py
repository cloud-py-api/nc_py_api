"""
Nextcloud API for working with users.
"""

from typing import Optional

from ._session import NcSessionBasic
from .misc import kwargs_to_dict

ENDPOINT_BASE = "/ocs/v1.php/cloud"
ENDPOINT = f"{ENDPOINT_BASE}/users"


class UsersAPI:
    """The class provides the user management API on the Nextcloud server.

    .. note:: In NextcloudApp mode, only ``get_list`` and ``get_details`` methods are available.
    """

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_list(
        self, mask: Optional[str] = "", limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[str]:
        """Returns list of user IDs.

        :param mask: user ID mask to apply.
        :param limit: limits the number of results.
        :param offset: offset of results.
        """

        data = kwargs_to_dict(["search", "limit", "offset"], search=mask, limit=limit, offset=offset)
        response_data = self._session.ocs(method="GET", path=ENDPOINT, params=data)
        return response_data["users"] if response_data else {}

    def get_details(self, user_id: str = "") -> dict:
        """Returns detailed user information.

        :param user_id: the identifier of the user about which information is to be returned.
        """

        if not user_id:
            user_id = self._session.user
        if not user_id:
            raise ValueError("user_id can not be empty.")
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/{user_id}")

    def create(self, user_id: str, **kwargs) -> None:
        """Create a new user on the Nextcloud server.

        :param user_id: id of the user to create.
        :param kwargs: See below.

        Additionally supported arguments:

            * ``password`` - password that should be set for user.
            * ``email`` - email of the new user. If ``password`` is not provided, then this field should be filled.
            * ``displayname`` - display name of the new user.
            * ``groups`` - groups IDs to which user belongs.
            * ``subadmin`` - boolean indicating is user should be the subadmin.
            * ``quota`` - quota for the user, if needed.
            * ``language`` - default language for the user.
        """

        password = kwargs.get("password", None)
        email = kwargs.get("email", None)
        if not password and not email:
            raise ValueError("Either password or email must be set")
        data = {"userid": user_id}
        for k in ("password", "displayname", "email", "groups", "subadmin", "quota", "language"):
            if k in kwargs:
                data[k] = kwargs[k]
        self._session.ocs(method="POST", path=ENDPOINT, params=data)

    def delete(self, user_id: str) -> None:
        """Deletes user from the Nextcloud server.

        :param user_id: id of the user.
        """

        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{user_id}")

    def enable(self, user_id: str) -> None:
        """Enables user on the Nextcloud server.

        :param user_id: id of the user.
        """

        self._session.ocs(method="PUT", path=f"{ENDPOINT}/{user_id}/enable")

    def disable(self, user_id: str) -> None:
        """Disables user on the Nextcloud server.

        :param user_id: id of the user.
        """

        self._session.ocs(method="PUT", path=f"{ENDPOINT}/{user_id}/disable")

    def resend_welcome_email(self, user_id: str) -> None:
        """Send welcome email for specified user again.

        :param user_id: id of the user.
        """

        self._session.ocs(method="POST", path=f"{ENDPOINT}/{user_id}/welcome")

    def editable_fields(self) -> list[str]:
        """Returns user fields that avalaible for edit."""

        return self._session.ocs(method="GET", path=f"{ENDPOINT_BASE}/user/fields")

    def edit(self, user_id: str, **kwargs) -> None:
        """Edits user metadata.

        :param user_id: id of the user.
        :param kwargs: dictionary where keys are values from ``editable_fields`` method, and values to set.
        """

        for k, v in kwargs.items():
            self._session.ocs(method="PUT", path=f"{ENDPOINT}/{user_id}", params={"key": k, "value": v})

    def add_to_group(self, user_id: str, group_id: str) -> None:
        """Adds user to the group.

        :param user_id: ID of the user.
        :param group_id: the destination group to which add user to.
        """

        self._session.ocs(method="POST", path=f"{ENDPOINT}/{user_id}/groups", params={"groupid": group_id})

    def remove_from_group(self, user_id: str, group_id: str) -> None:
        """Removes user from the group.

        :param user_id: ID of the user.
        :param group_id: group from which remove user.
        """

        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{user_id}/groups", params={"groupid": group_id})

    def promote_to_subadmin(self, user_id: str, group_id: str) -> None:
        """Makes user admin of the group.

        :param user_id: ID of the user.
        :param group_id: group where user should become administrator.
        """

        self._session.ocs(method="POST", path=f"{ENDPOINT}/{user_id}/subadmins", params={"groupid": group_id})

    def demote_from_subadmin(self, user_id: str, group_id: str) -> None:
        """Removes user from the admin role of the group.

        :param user_id: ID of the user.
        :param group_id: group where user should be removed from administrators.
        """

        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{user_id}/subadmins", params={"groupid": group_id})
