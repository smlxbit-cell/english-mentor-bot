"""AI dialogue partner (role-play with a story character).

Turn-limited and budget-aware so free-form chat stays cheap.
"""

from __future__ import annotations

from collections.abc import Sequence

from django.conf import settings

from . import economy
from .prompts import build_dialogue_system
from .registry import get_provider
from .types import ChatMessage


class DialoguePartner:
    def __init__(self, provider=None):
        self._provider = provider

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_provider()
        return self._provider

    async def reply(
        self,
        *,
        history: Sequence[ChatMessage],
        character_name: str = 'Emma',
        character_role: str = 'friendly guide',
        personality: str = '',
        speaking_style: str = '',
        level: str = 'a2',
        situation: str = 'casual small talk',
        user_key: str | None = None,
    ) -> str:
        if not economy.can_spend(user_key):
            return (
                "Let's continue this later 🙂 "
                "(на сегодня лимит бесплатных AI-реплик исчерпан)"
            )

        system = build_dialogue_system(
            character_name=character_name,
            character_role=character_role,
            personality=personality,
            speaking_style=speaking_style,
            level=level,
            situation=situation,
        )

        # Keep only the last few messages to bound token usage.
        window = list(history)[-settings.AI_HISTORY_MESSAGES:]
        messages = [system, *window]

        try:
            chat = await self.provider.chat(
                messages,
                max_tokens=min(settings.AI_MAX_OUTPUT_TOKENS, 120),
                temperature=0.6,
            )
        except Exception:  # noqa: BLE001
            return f"Sorry, I didn't catch that. Could you say it again?"

        economy.register_spend(user_key)
        return chat.text
