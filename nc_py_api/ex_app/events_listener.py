"""Nextcloud API for registering Events listeners for ExApps."""

import dataclasses

from .._exceptions import NextcloudExceptionNotFound
from .._misc import require_capabilities
from .._session import AsyncNcSessionApp, NcSessionApp

_EP_SUFFIX: str = "events_listener"


@dataclasses.dataclass
class EventsListener:
    """EventsListener description."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def event_type(self) -> str:
        """Main type of event, e.g. ``node_event``."""
        return self._raw_data["event_type"]

    @property
    def event_subtypes(self) -> str:
        """Subtypes for which fire event, e.g. ``NodeCreatedEvent``, ``NodeDeletedEvent``."""
        return self._raw_data["event_subtypes"]

    @property
    def action_handler(self) -> str:
        """Relative ExApp url which will be called by Nextcloud."""
        return self._raw_data["action_handler"]

    def __repr__(self):
        return f"<{self.__class__.__name__} event_type={self.event_type}, handler={self.action_handler}>"


class EventsListenerAPI:
    """API for registering Events listeners, avalaible as **nc.events_handler.<method>**."""

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(
        self,
        event_type: str,
        callback_url: str,
        event_subtypes: list[str] | None = None,
    ) -> None:
        """Registers or edits the events listener."""
        if event_subtypes is None:
            event_subtypes = []
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "eventType": event_type,
            "actionHandler": callback_url,
            "eventSubtypes": event_subtypes,
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    def unregister(self, event_type: str, not_fail=True) -> None:
        """Removes the events listener."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs(
                "DELETE",
                f"{self._session.ae_url}/{_EP_SUFFIX}",
                params={"eventType": event_type},
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def get_entry(self, event_type: str) -> EventsListener | None:
        """Get information about the event listener."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            return EventsListener(
                self._session.ocs(
                    "GET",
                    f"{self._session.ae_url}/{_EP_SUFFIX}",
                    params={"eventType": event_type},
                )
            )
        except NextcloudExceptionNotFound:
            return None


class AsyncEventsListenerAPI:
    """API for registering Events listeners, avalaible as **nc.events_handler.<method>**."""

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register(
        self,
        event_type: str,
        callback_url: str,
        event_subtypes: list[str] | None = None,
    ) -> None:
        """Registers or edits the events listener."""
        if event_subtypes is None:
            event_subtypes = []
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "eventType": event_type,
            "actionHandler": callback_url,
            "eventSubtypes": event_subtypes,
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    async def unregister(self, event_type: str, not_fail=True) -> None:
        """Removes the events listener."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs(
                "DELETE",
                f"{self._session.ae_url}/{_EP_SUFFIX}",
                params={"eventType": event_type},
            )
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def get_entry(self, event_type: str) -> EventsListener | None:
        """Get information about the event listener."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            return EventsListener(
                await self._session.ocs(
                    "GET",
                    f"{self._session.ae_url}/{_EP_SUFFIX}",
                    params={"eventType": event_type},
                )
            )
        except NextcloudExceptionNotFound:
            return None
