"""OpenAI-compatible /audio/speech TTS (uses your OPENAI_* credentials).

Works through the same base URL/key as the chat provider (e.g. aitunnel).
Not free, but cheap and high quality when you have a budget.
"""

from __future__ import annotations

import httpx
from django.conf import settings

from .base import TTSProvider, TTSResult


class OpenAITTSError(RuntimeError):
    pass


class OpenAITTS(TTSProvider):
    name = 'openai'

    def __init__(self, voice: str | None = None, model: str | None = None):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL.rstrip('/')
        self.model = model or settings.OPENAI_TTS_MODEL
        self.voice = voice or settings.OPENAI_TTS_VOICE
        self.timeout = settings.TTS_TIMEOUT_SECONDS
        if not self.api_key:
            raise OpenAITTSError('OPENAI_API_KEY is not configured.')

    async def synthesize(self, text: str, *, voice: str | None = None) -> TTSResult:
        text = (text or '').strip()
        if not text:
            return TTSResult(b'', ok=False)

        payload = {
            'model': self.model,
            'voice': voice or self.voice,
            'input': text,
            'response_format': 'mp3',
        }
        headers = {'Authorization': f'Bearer {self.api_key}'}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f'{self.base_url}/audio/speech', json=payload, headers=headers,
            )

        if response.status_code >= 400:
            raise OpenAITTSError(
                f'TTS request failed ({response.status_code}): {response.text[:200]}'
            )
        return TTSResult(response.content, fmt='mp3', ok=bool(response.content))
