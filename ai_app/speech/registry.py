"""STT provider factory. Selects backend from settings."""

from __future__ import annotations

from django.conf import settings

from .base import STTProvider
from .mock import MockSTT

_OPENAI_STT = frozenset({'whisper', 'openai', 'openai_whisper', 'openai-whisper'})


def get_stt_provider(name: str | None = None) -> STTProvider:
    provider = (name or settings.STT_PROVIDER or 'mock').lower()

    if provider in _OPENAI_STT:
        from .whisper import OpenAIWhisperSTT, OpenAIWhisperSTTError

        try:
            return OpenAIWhisperSTT()
        except OpenAIWhisperSTTError:
            return MockSTT()

    if provider == 'yandex':
        from .yandex import YandexSTT, YandexSTTError

        try:
            return YandexSTT()
        except YandexSTTError:
            return MockSTT()

    return MockSTT()


def get_tutor_stt_provider(*, stt_model: str | None = None) -> STTProvider:
    """STT for 💬 Наставник — Yandex when configured, else Whisper via AITUNNEL."""
    global_provider = (settings.STT_PROVIDER or '').lower()
    tutor_explicit = (getattr(settings, 'STT_TUTOR_PROVIDER', None) or '').strip().lower()

    if tutor_explicit == 'yandex' or global_provider == 'yandex':
        yandex = get_stt_provider('yandex')
        if yandex.name != 'mock':
            return yandex

    if stt_model and settings.OPENAI_API_KEY and global_provider != 'yandex':
        from .whisper import OpenAIWhisperSTT, OpenAIWhisperSTTError
        try:
            return OpenAIWhisperSTT(model=stt_model)
        except OpenAIWhisperSTTError:
            pass
    if tutor_explicit and tutor_explicit not in ('yandex', 'default', 'auto'):
        return get_stt_provider(tutor_explicit)
    if settings.OPENAI_API_KEY and global_provider != 'yandex':
        whisper = get_stt_provider('whisper')
        if whisper.name != 'mock':
            return whisper
    if settings.STT_YANDEX_FALLBACK or settings.YANDEX_SPEECHKIT_API_KEY:
        yandex = get_stt_provider('yandex')
        if yandex.name != 'mock':
            return yandex
    return MockSTT()
