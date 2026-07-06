"""TTS provider factory. Selects backend from settings.TTS_PROVIDER."""

from __future__ import annotations

from django.conf import settings

from .base import TTSProvider
from .mock import MockTTS


def get_tts_provider(name: str | None = None) -> TTSProvider:
    if not settings.TTS_ENABLED:
        return MockTTS()

    provider = (name or settings.TTS_PROVIDER or 'edge').lower()

    if provider == 'edge':
        from .edge import EdgeTTS, EdgeTTSError
        try:
            return EdgeTTS()
        except EdgeTTSError:
            return MockTTS()

    if provider == 'openai':
        from .openai_tts import OpenAITTS, OpenAITTSError
        try:
            return OpenAITTS()
        except OpenAITTSError:
            return MockTTS()

    return MockTTS()
