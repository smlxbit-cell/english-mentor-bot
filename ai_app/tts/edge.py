"""Free neural TTS via Microsoft Edge voices (edge-tts).

No API key required. Natural voices (e.g. en-US-AriaNeural, en-GB-SoniaNeural).
Install:  pip install edge-tts
"""

from __future__ import annotations

from django.conf import settings

from .base import TTSProvider, TTSResult


class EdgeTTSError(RuntimeError):
    pass


class EdgeTTS(TTSProvider):
    name = 'edge'

    def __init__(self, voice: str | None = None):
        self.voice = voice or settings.TTS_VOICE

    async def synthesize(self, text: str, *, voice: str | None = None) -> TTSResult:
        text = (text or '').strip()
        if not text:
            return TTSResult(b'', ok=False)

        try:
            import edge_tts
        except ImportError as exc:  # pragma: no cover
            raise EdgeTTSError('edge-tts is not installed (pip install edge-tts).') from exc

        communicate = edge_tts.Communicate(text, voice or self.voice)
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk.get('type') == 'audio' and chunk.get('data'):
                audio.extend(chunk['data'])

        return TTSResult(bytes(audio), fmt='mp3', ok=bool(audio))
