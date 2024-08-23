"""Nextcloud API for AI Providers."""

from ..._session import AsyncNcSessionApp, NcSessionApp
from .task_processing import _AsyncTaskProcessingProviderAPI, _TaskProcessingProviderAPI


class ProvidersApi:
    """Class that encapsulates all AI Providers functionality."""

    task_processing: _TaskProcessingProviderAPI
    """TaskProcessing Provider API."""

    def __init__(self, session: NcSessionApp):
        self.task_processing = _TaskProcessingProviderAPI(session)


class AsyncProvidersApi:
    """Class that encapsulates all AI Providers functionality."""

    task_processing: _AsyncTaskProcessingProviderAPI
    """TaskProcessing Provider API."""

    def __init__(self, session: AsyncNcSessionApp):
        self.task_processing = _AsyncTaskProcessingProviderAPI(session)
