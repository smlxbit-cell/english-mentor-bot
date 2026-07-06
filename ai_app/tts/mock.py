"""Offline TTS stub: produces no audio so the bot degrades gracefully."""

from __future__ import annotations

from .base import TTSProvider, TTSResult


class MockTTS(TTSProvider):
    name = 'mock'

    async def synthesize(self, text: str, *, voice: str | None = None) -> TTSResult:
        return TTSResult(b'', ok=False)
