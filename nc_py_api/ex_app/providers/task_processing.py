"""Nextcloud API for declaring TaskProcessing provider."""

import contextlib
import dataclasses

from ..._exceptions import NextcloudException, NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import AsyncNcSessionApp, NcSessionApp

_EP_SUFFIX: str = "ai_provider/task_processing"


@dataclasses.dataclass
class TaskProcessingProvider:
    """TaskProcessing provider description."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def name(self) -> str:
        """Unique ID for the provider."""
        return self._raw_data["name"]

    @property
    def display_name(self) -> str:
        """Providers display name."""
        return self._raw_data["display_name"]

    @property
    def task_type(self) -> str:
        """The TaskType provided by this provider."""
        return self._raw_data["task_type"]

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, type={self.task_type}>"


class _TaskProcessingProviderAPI:
    """API for TaskProcessing providers, available as **nc.providers.task_processing.<method>**."""

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(self, name: str, display_name: str, task_type: str) -> None:
        """Registers or edit the TaskProcessing provider."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "taskType": task_type,
        }
        self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes TaskProcessing provider."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def next_task(self, provider_ids: [str], task_types: [str]):
        """Get the next task processing task from Nextcloud"""
        with contextlib.suppress(NextcloudException):
            return self._session.ocs(
                "GET",
                "/ocs/v2.php/taskprocessing/tasks_provider/next",
                json={"providerIds": provider_ids, "taskTypeIds": task_types},
            )

    def report_result(self, task_id: int, output: [str, str] = None, error_message: str = None) -> None:
        """Report results of the task processing to Nextcloud."""
        with contextlib.suppress(NextcloudException):
            return self._session.ocs(
                "POST",
                f"/ocs/v2.php/taskprocessing/tasks_provider/{task_id}/result",
                json={"taskId": task_id, "output": output, "errorMessage": error_message},
            )


class _AsyncTaskProcessingProviderAPI:
    """Async API for TaskProcessing providers."""

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register(self, name: str, display_name: str, task_type: str) -> None:
        """Registers or edit the TaskProcessing provider."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "taskType": task_type,
        }
        await self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    async def unregister(self, name: str, not_fail=True) -> None:
        """Removes TaskProcessing provider."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def next_task(self, provider_ids: [str], task_types: [str]):
        """Get the next task processing task from Nextcloud"""
        with contextlib.suppress(NextcloudException):
            return await self._session.ocs(
                "GET",
                "/ocs/v2.php/taskprocessing/tasks_provider/next",
                json={"providerIds": provider_ids, "taskTypeIds": task_types},
            )

    async def report_result(self, task_id: int, output: [str, str] = None, error_message: str = None) -> None:
        """Report results of the task processing to Nextcloud."""
        require_capabilities("app_api", await self._session.capabilities)
        with contextlib.suppress(NextcloudException):
            await self._session.ocs(
                "POST",
                f"/ocs/v2.php/taskprocessing/tasks_provider/{task_id}/result",
                json={"taskId": task_id, "output": output, "errorMessage": error_message},
            )
