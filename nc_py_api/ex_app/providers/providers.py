"""Nextcloud API for AI Providers."""

from ..._session import AsyncNcSessionApp, NcSessionApp
from .speech_to_text import _AsyncSpeechToTextProviderAPI, _SpeechToTextProviderAPI
from .text_processing import _AsyncTextProcessingProviderAPI, _TextProcessingProviderAPI


class ProvidersApi:
    """Class that encapsulates all AI Providers functionality."""

    speech_to_text: _SpeechToTextProviderAPI
    """SpeechToText Provider API."""
    text_processing: _TextProcessingProviderAPI
    """TextProcessing Provider API."""

    def __init__(self, session: NcSessionApp):
        self.speech_to_text = _SpeechToTextProviderAPI(session)
        self.text_processing = _TextProcessingProviderAPI(session)


class AsyncProvidersApi:
    """Class that encapsulates all AI Providers functionality."""

    speech_to_text: _AsyncSpeechToTextProviderAPI
    """SpeechToText Provider API."""
    text_processing: _AsyncTextProcessingProviderAPI
    """TextProcessing Provider API."""

    def __init__(self, session: AsyncNcSessionApp):
        self.speech_to_text = _AsyncSpeechToTextProviderAPI(session)
        self.text_processing = _AsyncTextProcessingProviderAPI(session)
