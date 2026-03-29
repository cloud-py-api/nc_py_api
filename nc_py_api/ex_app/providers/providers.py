"""Nextcloud API for AI Providers."""

from ..._session import AsyncNcSessionApp
from .task_processing import _TaskProcessingProviderAPI


class ProvidersApi:
    """Class that encapsulates all AI Providers functionality."""

    task_processing: _TaskProcessingProviderAPI
    """TaskProcessing Provider API."""

    def __init__(self, session: AsyncNcSessionApp):
        self.task_processing = _TaskProcessingProviderAPI(session)
