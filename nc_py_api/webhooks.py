"""Nextcloud Webhooks API."""

import dataclasses

from ._misc import clear_from_params_empty  # , require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class WebhookInfo:
    """Information about the Webhook."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def webhook_id(self) -> int:
        """`ID` of the webhook."""
        return self._raw_data["id"]

    @property
    def app_id(self) -> str:
        """`ID` of the ExApp that registered webhook."""
        return self._raw_data["appId"] if self._raw_data["appId"] else ""

    @property
    def user_id(self) -> str:
        """`UserID` if webhook was registered in user context."""
        return self._raw_data["userId"] if self._raw_data["userId"] else ""

    @property
    def http_method(self) -> str:
        """HTTP method used to call webhook."""
        return self._raw_data["httpMethod"]

    @property
    def uri(self) -> str:
        """URL address that will be called for this webhook."""
        return self._raw_data["uri"]

    @property
    def event(self) -> str:
        """Nextcloud PHP event that triggers this webhook."""
        return self._raw_data["event"]

    @property
    def event_filter(self):
        """Mongo filter to apply to the serialized data to decide if firing."""
        return self._raw_data["eventFilter"]

    @property
    def user_id_filter(self) -> str:
        """Currently unknown."""
        return self._raw_data["userIdFilter"]

    @property
    def headers(self) -> dict:
        """Headers that should be added to request when calling webhook."""
        return self._raw_data["headers"] if self._raw_data["headers"] else {}

    @property
    def auth_method(self) -> str:
        """Currently unknown."""
        return self._raw_data["authMethod"]

    @property
    def auth_data(self) -> dict:
        """Currently unknown."""
        return self._raw_data["authData"] if self._raw_data["authData"] else {}

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.webhook_id}, event={self.event}>"


class _WebhooksAPI:
    """The class provides the application management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/webhook_listeners/api/v1/webhooks"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def get_list(self, uri_filter: str = "") -> list[WebhookInfo]:
        params = {"uri": uri_filter} if uri_filter else {}
        return [WebhookInfo(i) for i in self._session.ocs("GET", f"{self._ep_base}", params=params)]

    def get_entry(self, webhook_id: int) -> WebhookInfo:
        return WebhookInfo(self._session.ocs("GET", f"{self._ep_base}/{webhook_id}"))

    def register(
        self,
        http_method: str,
        uri: str,
        event: str,
        event_filter: dict | None = None,
        user_id_filter: str = "",
        headers: dict | None = None,
        auth_method: str = "none",
        auth_data: dict | None = None,
    ):
        params = {
            "httpMethod": http_method,
            "uri": uri,
            "event": event,
            "eventFilter": event_filter,
            "userIdFilter": user_id_filter,
            "headers": headers,
            "authMethod": auth_method,
            "authData": auth_data,
        }
        clear_from_params_empty(["eventFilter", "userIdFilter", "headers", "authMethod", "authData"], params)
        return WebhookInfo(self._session.ocs("POST", f"{self._ep_base}", json=params))

    def update(
        self,
        webhook_id: int,
        http_method: str,
        uri: str,
        event: str,
        event_filter: dict | None = None,
        user_id_filter: str = "",
        headers: dict | None = None,
        auth_method: str = "none",
        auth_data: dict | None = None,
    ):
        params = {
            "id": webhook_id,
            "httpMethod": http_method,
            "uri": uri,
            "event": event,
            "eventFilter": event_filter,
            "userIdFilter": user_id_filter,
            "headers": headers,
            "authMethod": auth_method,
            "authData": auth_data,
        }
        clear_from_params_empty(["eventFilter", "userIdFilter", "headers", "authMethod", "authData"], params)
        return WebhookInfo(self._session.ocs("POST", f"{self._ep_base}/{webhook_id}", json=params))

    def unregister(self, webhook_id: int) -> bool:
        return self._session.ocs("DELETE", f"{self._ep_base}/{webhook_id}")


class _AsyncWebhooksAPI:
    """The class provides the async application management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/webhooks"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    async def get_list(self, uri_filter: str = "") -> list[WebhookInfo]:
        params = {"uri": uri_filter} if uri_filter else {}
        return [WebhookInfo(i) for i in await self._session.ocs("GET", f"{self._ep_base}", params=params)]

    async def get_entry(self, webhook_id: int) -> WebhookInfo:
        return WebhookInfo(await self._session.ocs("GET", f"{self._ep_base}/{webhook_id}"))

    async def register(
        self,
        http_method: str,
        uri: str,
        event: str,
        event_filter: dict | None = None,
        user_id_filter: str = "",
        headers: dict | None = None,
        auth_method: str = "none",
        auth_data: dict | None = None,
    ):
        params = {
            "httpMethod": http_method,
            "uri": uri,
            "event": event,
            "eventFilter": event_filter,
            "userIdFilter": user_id_filter,
            "headers": headers,
            "authMethod": auth_method,
            "authData": auth_data,
        }
        clear_from_params_empty(["eventFilter", "userIdFilter", "headers", "authMethod", "authData"], params)
        return WebhookInfo(await self._session.ocs("POST", f"{self._ep_base}", json=params))

    async def update(
        self,
        webhook_id: int,
        http_method: str,
        uri: str,
        event: str,
        event_filter: dict | None = None,
        user_id_filter: str = "",
        headers: dict | None = None,
        auth_method: str = "none",
        auth_data: dict | None = None,
    ):
        params = {
            "id": webhook_id,
            "httpMethod": http_method,
            "uri": uri,
            "event": event,
            "eventFilter": event_filter,
            "userIdFilter": user_id_filter,
            "headers": headers,
            "authMethod": auth_method,
            "authData": auth_data,
        }
        clear_from_params_empty(["eventFilter", "userIdFilter", "headers", "authMethod", "authData"], params)
        return WebhookInfo(await self._session.ocs("POST", f"{self._ep_base}/{webhook_id}", json=params))

    async def unregister(self, webhook_id: int) -> bool:
        return await self._session.ocs("DELETE", f"{self._ep_base}/{webhook_id}")
