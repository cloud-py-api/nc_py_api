"""Nextcloud API for declaring TaskProcessing provider."""

import contextlib
import dataclasses
import typing
from enum import IntEnum

from pydantic import RootModel
from pydantic.dataclasses import dataclass

from ..._exceptions import NextcloudException, NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import AsyncNcSessionApp, NcSessionApp

_EP_SUFFIX: str = "ai_provider/task_processing"


class ShapeType(IntEnum):
    """Enum for shape types."""

    NUMBER = 0
    TEXT = 1
    IMAGE = 2
    AUDIO = 3
    VIDEO = 4
    FILE = 5
    ENUM = 6
    LIST_OF_NUMBERS = 10
    LIST_OF_TEXTS = 11
    LIST_OF_IMAGES = 12
    LIST_OF_AUDIOS = 13
    LIST_OF_VIDEOS = 14
    LIST_OF_FILES = 15


@dataclass
class ShapeEnumValue:
    """Data object for input output shape enum slot value."""

    name: str
    """Name of the enum slot value which will be displayed in the UI"""
    value: str
    """Value of the enum slot value"""


@dataclass
class ShapeDescriptor:
    """Data object for input output shape entries."""

    name: str
    """Name of the shape entry"""
    description: str
    """Description of the shape entry"""
    shape_type: ShapeType
    """Type of the shape entry"""


@dataclass
class TaskType:
    """TaskType description for the provider."""

    id: str
    """The unique ID for the task type."""
    name: str
    """The localized name of the task type."""
    description: str
    """The localized description of the task type."""
    input_shape: list[ShapeDescriptor]
    """The input shape of the task."""
    output_shape: list[ShapeDescriptor]
    """The output shape of the task."""


@dataclass
class TaskProcessingProvider:

    id: str
    """Unique ID for the provider."""
    name: str
    """The localized name of this provider"""
    task_type: str
    """The TaskType provided by this provider."""
    expected_runtime: int = dataclasses.field(default=0)
    """Expected runtime of the task in seconds."""
    optional_input_shape: list[ShapeDescriptor] = dataclasses.field(default_factory=list)
    """Optional input shape of the task."""
    optional_output_shape: list[ShapeDescriptor] = dataclasses.field(default_factory=list)
    """Optional output shape of the task."""
    input_shape_enum_values: dict[str, list[ShapeEnumValue]] = dataclasses.field(default_factory=dict)
    """The option dict for each input shape ENUM slot."""
    input_shape_defaults: dict[str, str | int | float] = dataclasses.field(default_factory=dict)
    """The default values for input shape slots."""
    optional_input_shape_enum_values: dict[str, list[ShapeEnumValue]] = dataclasses.field(default_factory=dict)
    """The option list for each optional input shape ENUM slot."""
    optional_input_shape_defaults: dict[str, str | int | float] = dataclasses.field(default_factory=dict)
    """The default values for optional input shape slots."""
    output_shape_enum_values: dict[str, list[ShapeEnumValue]] = dataclasses.field(default_factory=dict)
    """The option list for each output shape ENUM slot."""
    optional_output_shape_enum_values: dict[str, list[ShapeEnumValue]] = dataclasses.field(default_factory=dict)
    """The option list for each optional output shape ENUM slot."""

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}, type={self.task_type}>"


class _TaskProcessingProviderAPI:
    """API for TaskProcessing providers, available as **nc.providers.task_processing.<method>**."""

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(
        self,
        provider: TaskProcessingProvider,
        custom_task_type: TaskType | None = None,
    ) -> None:
        """Registers or edit the TaskProcessing provider."""
        require_capabilities("app_api", self._session.capabilities)
        params = {
            "provider": RootModel(provider).model_dump(),
            **({"customTaskType": RootModel(custom_task_type).model_dump()} if custom_task_type else {}),
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
        self,
        provider: TaskProcessingProvider,
        custom_task_type: TaskType | None = None,
    ) -> None:
        """Registers or edit the TaskProcessing provider."""
        require_capabilities("app_api", await self._session.capabilities)
        params = {
            "provider": RootModel(provider).model_dump(),
            **({"customTaskType": RootModel(custom_task_type).model_dump()} if custom_task_type else {}),
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
