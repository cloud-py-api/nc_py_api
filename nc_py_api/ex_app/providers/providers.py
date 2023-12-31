"""Nextcloud API for AI Providers."""

from ..._session import AsyncNcSessionApp, NcSessionApp
from .speech_to_text import _AsyncSpeechToTextProviderAPI, _SpeechToTextProviderAPI


class ProvidersApi:
    """Class that encapsulates all AI Providers functionality."""

    speech_to_text: _SpeechToTextProviderAPI
    """SpeechToText Provider API."""

    def __init__(self, session: NcSessionApp):
        self.speech_to_text = _SpeechToTextProviderAPI(session)


class AsyncProvidersApi:
    """Class that encapsulates all AI Providers functionality."""

    speech_to_text: _AsyncSpeechToTextProviderAPI
    """SpeechToText Provider API."""

    def __init__(self, session: AsyncNcSessionApp):
        self.speech_to_text = _AsyncSpeechToTextProviderAPI(session)
