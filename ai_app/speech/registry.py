"""STT provider factory. Selects backend from settings.STT_PROVIDER."""

from __future__ import annotations

from django.conf import settings

from .base import STTProvider
from .mock import MockSTT


def get_stt_provider(name: str | None = None) -> STTProvider:
    provider = (name or settings.STT_PROVIDER or 'mock').lower()

    if provider == 'yandex':
        from .yandex import YandexSTT, YandexSTTError

        try:
            return YandexSTT()
        except YandexSTTError:
            return MockSTT()

    return MockSTT()
