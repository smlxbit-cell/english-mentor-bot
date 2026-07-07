"""OpenAI Whisper STT via an OpenAI-compatible proxy (same OPENAI_* as chat/TTS).

Works with AITUNNEL and other gateways — set OPENAI_WHISPER_MODEL to any catalog slug,
e.g. whisper-large-v3-turbo, gpt-4o-mini-transcribe.
Docs: https://platform.openai.com/docs/api-reference/audio/createTranscription
"""

from __future__ import annotations

import httpx
from django.conf import settings

from .base import STTProvider, Transcript


class OpenAIWhisperSTTError(RuntimeError):
    pass


def _map_lang(lang: str) -> str | None:
    """Map SpeechKit-style lang to ISO-639-1 for Whisper, or None = auto-detect."""
    raw = (lang or '').strip().lower()
    if not raw or raw in {'auto', 'mixed'}:
        return None
    if raw.startswith('ru'):
        return 'ru'
    if raw.startswith('en'):
        return 'en'
    if len(raw) == 2:
        return raw
    return None


def _whisper_model_candidates(primary: str | None = None) -> list[str]:
    """Build try-order: tier primary, then env default, then fallbacks."""
    models: list[str] = []
    default = settings.OPENAI_WHISPER_MODEL.strip()
    for raw in (
        primary,
        default,
        *settings.OPENAI_WHISPER_FALLBACK_MODELS.split(','),
    ):
        name = (raw or '').strip()
        if name and name not in models:
            models.append(name)
    return models


class OpenAIWhisperSTT(STTProvider):
    name = 'whisper'

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip('/')
        self.model = model or settings.OPENAI_WHISPER_MODEL
        self.timeout = settings.OPENAI_STT_TIMEOUT_SECONDS
        if not self.api_key:
            raise OpenAIWhisperSTTError('OPENAI_API_KEY is not configured.')

    async def _call_model(
        self,
        client: httpx.AsyncClient,
        *,
        model: str,
        audio: bytes,
        whisper_lang: str | None,
    ) -> str:
        data: dict[str, str] = {
            'model': model,
            'response_format': 'json',
        }
        if whisper_lang:
            data['language'] = whisper_lang

        headers = {'Authorization': f'Bearer {self.api_key}'}
        files = {'file': ('voice.ogg', audio, 'audio/ogg')}
        response = await client.post(
            f'{self.base_url}/audio/transcriptions',
            data=data,
            files=files,
            headers=headers,
        )
        if response.status_code >= 400:
            raise OpenAIWhisperSTTError(
                f'{model} failed ({response.status_code}): {response.text[:300]}'
            )
        payload = response.json() if response.content else {}
        return ((payload.get('text') if isinstance(payload, dict) else '') or '').strip()

    async def transcribe(
        self,
        audio: bytes,
        *,
        lang: str = 'en-US',
        short_utterance: bool = False,
    ) -> Transcript:
        del short_utterance  # Whisper has no short-utterance mode
        if not audio:
            return Transcript(text='', provider=self.name, ok=False)

        whisper_lang = _map_lang(lang)
        errors: list[str] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for model in _whisper_model_candidates(self.model):
                try:
                    text = await self._call_model(
                        client, model=model, audio=audio, whisper_lang=whisper_lang,
                    )
                    if text:
                        return Transcript(text=text, provider=self.name, ok=True)
                except OpenAIWhisperSTTError as exc:
                    errors.append(str(exc))

        detail = errors[0] if errors else 'empty transcript'
        raise OpenAIWhisperSTTError(detail)
