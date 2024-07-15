"""Nextcloud API for declaring TaskProcessing provider."""

import contextlib
import dataclasses
import typing

from ..._exceptions import NextcloudException, NextcloudExceptionNotFound
from ..._misc import clear_from_params_empty, require_capabilities
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

    def register(
        self, name: str, display_name: str, task_type: str, custom_task_type: dict[str, typing.Any] | None = None
    ) -> None:
        """Registers or edit the TaskProcessing provider."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "taskType": task_type,
            "customTaskType": custom_task_type,
        }
        clear_from_params_empty(["customTaskType"], params)
        self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes TaskProcessing provider."""
        require_capabilities("app_api", self._session.capabilities)
        try:
            self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    def next_task(self, provider_ids: list[str], task_types: list[str]) -> dict[str, typing.Any]:
        """Get the next task processing task from Nextcloud."""
        with contextlib.suppress(NextcloudException):
            if r := self._session.ocs(
                "GET",
                "/ocs/v2.php/taskprocessing/tasks_provider/next",
                json={"providerIds": provider_ids, "taskTypeIds": task_types},
            ):
                return r
        return {}

    def set_progress(self, task_id: int, progress: float) -> dict[str, typing.Any]:
        """Report new progress value of the task to Nextcloud. Progress should be in range from 0.0 to 100.0."""
        with contextlib.suppress(NextcloudException):
            if r := self._session.ocs(
                "POST",
                f"/ocs/v2.php/taskprocessing/tasks_provider/{task_id}/progress",
                json={"taskId": task_id, "progress": progress / 100.0},
            ):
                return r
        return {}

    def upload_result_file(self, task_id: int, file: bytes | str | typing.Any) -> int:
        """Uploads file and returns fileID that should be used in the ``report_result`` function.

        .. note:: ``file`` can be any file-like object.
        """
        return self._session.ocs(
            "POST",
            f"/ocs/v2.php/taskprocessing/tasks_provider/{task_id}/file",
            files={"file": file},
        )["fileId"]

    def report_result(
        self,
        task_id: int,
        output: dict[str, typing.Any] | None = None,
        error_message: str | None = None,
    ) -> dict[str, typing.Any]:
        """Report result of the task processing to Nextcloud."""
        with contextlib.suppress(NextcloudException):
            if r := self._session.ocs(
                "POST",
                f"/ocs/v2.php/taskprocessing/tasks_provider/{task_id}/result",
                json={"taskId": task_id, "output": output, "errorMessage": error_message},
            ):
                return r
        return {}


class _AsyncTaskProcessingProviderAPI:
    """Async API for TaskProcessing providers."""

    def __init__(self, session: AsyncNcSessionApp):
        self._session = session

    async def register(
        self, name: str, display_name: str, task_type: str, custom_task_type: dict[str, typing.Any] | None = None
    ) -> None:
        """Registers or edit the TaskProcessing provider."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "name": name,
            "displayName": display_name,
            "taskType": task_type,
            "customTaskType": custom_task_type,
        }
        clear_from_params_empty(["customTaskType"], params)
        await self._session.ocs("POST", f"{self._session.ae_url}/{_EP_SUFFIX}", json=params)

    async def unregister(self, name: str, not_fail=True) -> None:
        """Removes TaskProcessing provider."""
        require_capabilities("app_api", await self._session.capabilities)
        try:
            await self._session.ocs("DELETE", f"{self._session.ae_url}/{_EP_SUFFIX}", params={"name": name})
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None

    async def next_task(self, provider_ids: list[str], task_types: list[str]) -> dict[str, typing.Any]:
        """Get the next task processing task from Nextcloud."""
        with contextlib.suppress(NextcloudException):
            if r := await self._session.ocs(
                "GET",
                "/ocs/v2.php/taskprocessing/tasks_provider/next",
                json={"providerIds": provider_ids, "taskTypeIds": task_types},
            ):
                return r
        return {}

    async def set_progress(self, task_id: int, progress: float) -> dict[str, typing.Any]:
        """Report new progress value of the task to Nextcloud. Progress should be in range from 0.0 to 100.0."""
        with contextlib.suppress(NextcloudException):
            if r := await self._session.ocs(
                "POST",
                f"/ocs/v2.php/taskprocessing/tasks_provider/{task_id}/progress",
                json={"taskId": task_id, "progress": progress / 100.0},
            ):
                return r
        return {}

    async def upload_result_file(self, task_id: int, file: bytes | str | typing.Any) -> int:
        """Uploads file and returns fileID that should be used in the ``report_result`` function.

        .. note:: ``file`` can be any file-like object.
        """
        return (
            await self._session.ocs(
                "POST",
                f"/ocs/v2.php/taskprocessing/tasks_provider/{task_id}/file",
                files={"file": file},
            )
        )["fileId"]

    async def report_result(
        self,
        task_id: int,
        output: dict[str, typing.Any] | None = None,
        error_message: str | None = None,
    ) -> dict[str, typing.Any]:
        """Report result of the task processing to Nextcloud."""
        with contextlib.suppress(NextcloudException):
            if r := await self._session.ocs(
                "POST",
                f"/ocs/v2.php/taskprocessing/tasks_provider/{task_id}/result",
                json={"taskId": task_id, "output": output, "errorMessage": error_message},
            ):
                return r
        return {}
