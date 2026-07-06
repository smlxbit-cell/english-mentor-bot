"""Speech-to-text abstraction so the STT backend is swappable."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Transcript:
    text: str
    provider: str = ''
    ok: bool = True


class STTProvider(ABC):
    name: str = 'base'

    @abstractmethod
    async def transcribe(
        self,
        audio: bytes,
        *,
        lang: str = 'en-US',
        short_utterance: bool = False,
    ) -> Transcript:
        """Transcribe short audio (Telegram voice = OGG/Opus)."""
        raise NotImplementedError
