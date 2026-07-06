"""Offline mock provider for development without an API key.

Returns deterministic, well-formed responses so the whole flow (checking,
dialogue) can be exercised locally without spending tokens.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from .base import AIProvider
from .types import ChatMessage, ChatResult


class MockProvider(AIProvider):
    name = 'mock'

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == 'user'),
            '',
        )

        if json_mode:
            text = json.dumps(
                {
                    'is_correct': True,
                    'score': 0.8,
                    'feedback_ru': 'Хорошо! (демо-режим без реального AI)',
                    'correction': last_user.strip(),
                    'tip_ru': 'Подключите OPENAI_API_KEY для настоящей проверки.',
                },
                ensure_ascii=False,
            )
        else:
            text = 'Nice! (mock reply — set OPENAI_API_KEY for a real AI dialogue.)'

        approx = max(1, len(last_user) // 4)
        return ChatResult(
            text=text,
            input_tokens=approx,
            output_tokens=len(text) // 4,
            model='mock',
        )
