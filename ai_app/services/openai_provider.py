"""OpenAI chat-completions provider (default: gpt-4o-mini).

Uses httpx (already a dependency). Supports a custom base URL so requests can be
routed through a proxy/gateway when calling from Russia.
"""

from __future__ import annotations

from collections.abc import Sequence

import httpx
from django.conf import settings

from .base import AIProvider
from .types import ChatMessage, ChatResult


class OpenAIError(RuntimeError):
    pass


class OpenAIProvider(AIProvider):
    name = 'openai'

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip('/')
        self.timeout = timeout or settings.AI_TIMEOUT_SECONDS

        if not self.api_key:
            raise OpenAIError('OPENAI_API_KEY is not configured.')

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult:
        payload: dict = {
            'model': model or self.model,
            'messages': [m.as_dict() for m in messages],
            'temperature': temperature,
            'max_tokens': max_tokens or settings.AI_MAX_OUTPUT_TOKENS,
        }
        if json_mode:
            payload['response_format'] = {'type': 'json_object'}

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f'{self.base_url}/chat/completions',
                json=payload,
                headers=headers,
            )

        if response.status_code >= 400:
            raise OpenAIError(
                f'OpenAI request failed ({response.status_code}): {response.text[:400]}'
            )

        data = response.json()
        try:
            text = data['choices'][0]['message']['content'] or ''
        except (KeyError, IndexError) as exc:  # pragma: no cover - defensive
            raise OpenAIError(f'Unexpected OpenAI response: {data}') from exc

        usage = data.get('usage', {}) or {}
        return ChatResult(
            text=text.strip(),
            input_tokens=usage.get('prompt_tokens', 0),
            output_tokens=usage.get('completion_tokens', 0),
            model=data.get('model', self.model),
            raw=data,
        )
