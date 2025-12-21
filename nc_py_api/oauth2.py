"""Nextcloud API for working with OAuth2 clients."""

import dataclasses

from ._misc import check_capabilities, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class OAuth2Client:
    """Class representing one OAuth2 client."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def client_id(self) -> str:
        """Unique identifier of the OAuth2 client."""
        return self._raw_data["id"]

    @property
    def name(self) -> str:
        """Name of the OAuth2 client application."""
        return self._raw_data.get("name", "")

    @property
    def redirect_uri(self) -> str:
        """Redirect URI for the OAuth2 client."""
        return self._raw_data.get("redirect_uri", "")

    @property
    def client_secret(self) -> str:
        """Client secret (only available when creating a new client)."""
        return self._raw_data.get("client_secret", "")

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.client_id}, name={self.name}>"


class _OAuth2API:
    """Class providing the OAuth2 Client Management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/oauth2/api/v1/clients"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports OAuth2, False otherwise."""
        # OAuth2 is an admin API, check if oauth2 app is available
        return not check_capabilities("oauth2", self._session.capabilities)

    def get_list(self) -> list[OAuth2Client]:
        """Returns a list of all OAuth2 clients.

        .. note:: Requires admin privileges.
        """
        require_capabilities("oauth2", self._session.capabilities)
        result = self._session.ocs("GET", self._ep_base)
        return [OAuth2Client(i) for i in result]

    def create(self, name: str, redirect_uri: str) -> OAuth2Client:
        """Creates a new OAuth2 client.

        :param name: Name of the application.
        :param redirect_uri: Redirect URI for the OAuth2 client.
        :returns: OAuth2Client object with client_id and client_secret.

        .. note:: Requires admin privileges.
        """
        require_capabilities("oauth2", self._session.capabilities)
        if not name:
            raise ValueError("`name` parameter cannot be empty")
        if not redirect_uri:
            raise ValueError("`redirect_uri` parameter cannot be empty")
        result = self._session.ocs("POST", self._ep_base, json={"name": name, "redirect_uri": redirect_uri})
        return OAuth2Client(result)

    def delete(self, client_id: str) -> None:
        """Deletes an OAuth2 client.

        :param client_id: ID of the OAuth2 client to delete.

        .. note:: Requires admin privileges.
        """
        require_capabilities("oauth2", self._session.capabilities)
        if not client_id:
            raise ValueError("`client_id` parameter cannot be empty")
        self._session.ocs("DELETE", f"{self._ep_base}/{client_id}")


class _AsyncOAuth2API:
    """Class provides async OAuth2 Client Management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/oauth2/api/v1/clients"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports OAuth2, False otherwise."""
        # OAuth2 is an admin API, check if oauth2 app is available
        return not check_capabilities("oauth2", await self._session.capabilities)

    async def get_list(self) -> list[OAuth2Client]:
        """Returns a list of all OAuth2 clients.

        .. note:: Requires admin privileges.
        """
        require_capabilities("oauth2", await self._session.capabilities)
        result = await self._session.ocs("GET", self._ep_base)
        return [OAuth2Client(i) for i in result]

    async def create(self, name: str, redirect_uri: str) -> OAuth2Client:
        """Creates a new OAuth2 client.

        :param name: Name of the application.
        :param redirect_uri: Redirect URI for the OAuth2 client.
        :returns: OAuth2Client object with client_id and client_secret.

        .. note:: Requires admin privileges.
        """
        require_capabilities("oauth2", await self._session.capabilities)
        if not name:
            raise ValueError("`name` parameter cannot be empty")
        if not redirect_uri:
            raise ValueError("`redirect_uri` parameter cannot be empty")
        result = await self._session.ocs("POST", self._ep_base, json={"name": name, "redirect_uri": redirect_uri})
        return OAuth2Client(result)

    async def delete(self, client_id: str) -> None:
        """Deletes an OAuth2 client.

        :param client_id: ID of the OAuth2 client to delete.

        .. note:: Requires admin privileges.
        """
        require_capabilities("oauth2", await self._session.capabilities)
        if not client_id:
            raise ValueError("`client_id` parameter cannot be empty")
        await self._session.ocs("DELETE", f"{self._ep_base}/{client_id}")
