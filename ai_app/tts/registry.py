"""TTS provider factory. Selects backend from settings.TTS_PROVIDER."""

from __future__ import annotations

from django.conf import settings

from .base import TTSProvider
from .mock import MockTTS


def get_tts_provider(name: str | None = None) -> TTSProvider:
    if not settings.TTS_ENABLED:
        return MockTTS()

    provider = (name or settings.TTS_PROVIDER or 'openai').lower()

    if provider == 'openai':
        from .openai_tts import OpenAITTS, OpenAITTSError
        try:
            return OpenAITTS()
        except OpenAITTSError:
            pass

    if provider == 'edge':
        from .edge import EdgeTTS, EdgeTTSError
        try:
            return EdgeTTS()
        except EdgeTTSError:
            pass

    # Auto-fallback: openai → edge → mock
    if provider != 'openai' and settings.OPENAI_API_KEY:
        from .openai_tts import OpenAITTS, OpenAITTSError
        try:
            return OpenAITTS()
        except OpenAITTSError:
            pass

    if provider != 'edge':
        from .edge import EdgeTTS, EdgeTTSError
        try:
            return EdgeTTS()
        except EdgeTTSError:
            pass

    return MockTTS()
