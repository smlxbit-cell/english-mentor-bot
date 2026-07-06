"""Offline STT stub. Returns no transcript so the bot degrades gracefully.

The speaking flow should accept the attempt and encourage the learner rather
than block when transcription is unavailable.
"""

from __future__ import annotations

from .base import STTProvider, Transcript


class MockSTT(STTProvider):
    name = 'mock'

    async def transcribe(
        self,
        audio: bytes,
        *,
        lang: str = 'en-US',
        short_utterance: bool = False,
    ) -> Transcript:
        return Transcript(text='', provider=self.name, ok=False)
