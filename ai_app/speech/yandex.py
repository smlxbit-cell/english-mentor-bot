"""Yandex SpeechKit short-audio recognition (v1).

Telegram voice messages are OGG/Opus, which SpeechKit accepts directly.
Docs: https://yandex.cloud/docs/speechkit/stt/api/request-api
"""

from __future__ import annotations

import httpx
from django.conf import settings

from .base import STTProvider, Transcript

_ENDPOINT = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize'


class YandexSTTError(RuntimeError):
    pass


class YandexSTT(STTProvider):
    name = 'yandex'

    def __init__(self, api_key: str | None = None, folder_id: str | None = None):
        self.api_key = api_key or settings.YANDEX_SPEECHKIT_API_KEY
        self.folder_id = folder_id or settings.YANDEX_FOLDER_ID
        self.timeout = settings.YANDEX_STT_TIMEOUT_SECONDS
        if not self.api_key:
            raise YandexSTTError('YANDEX_SPEECHKIT_API_KEY is not configured.')

    async def transcribe(
        self,
        audio: bytes,
        *,
        lang: str = 'en-US',
        short_utterance: bool = False,
    ) -> Transcript:
        params = {
            'lang': lang,
            'format': 'oggopus',
            'profanityFilter': 'false',
        }
        if self.folder_id:
            params['folderId'] = self.folder_id
        if short_utterance:
            # Better for single words / very short clips from Telegram voice.
            params['topic'] = 'general'

        headers = {'Authorization': f'Api-Key {self.api_key}'}

        async def _call() -> str:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    _ENDPOINT,
                    params=params,
                    content=audio,
                    headers=headers,
                )
            if response.status_code >= 400:
                raise YandexSTTError(
                    f'SpeechKit failed ({response.status_code}): {response.text[:300]}'
                )
            return (response.json() or {}).get('result', '') or ''

        text = (await _call()).strip()
        if not text and short_utterance:
            # One retry — short clips sometimes return empty on first pass.
            text = (await _call()).strip()

        return Transcript(text=text, provider=self.name, ok=bool(text))
