"""Text-to-speech abstraction so the TTS backend is swappable."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSResult:
    audio: bytes
    fmt: str = 'mp3'  # 'mp3' | 'ogg'
    ok: bool = True


class TTSProvider(ABC):
    name: str = 'base'

    @abstractmethod
    async def synthesize(self, text: str, *, voice: str | None = None) -> TTSResult:
        """Synthesize English `text` into speech audio bytes."""
        raise NotImplementedError
