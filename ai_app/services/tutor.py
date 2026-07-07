"""English tutor chat (free-form help for learners)."""

from __future__ import annotations

from collections.abc import Sequence

from django.conf import settings

from .prompts import build_tutor_system
from .registry import get_provider
from .types import ChatMessage


class EnglishTutor:
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
        level: str = 'a2',
        check_english: bool = False,
        from_voice: bool = False,
        code_switch: bool = False,
        spirit_chat: bool = False,
        grammar_followup: bool = False,
        followup_target: str = '',
    ) -> str:
        system = build_tutor_system(
            level=level, check_english=check_english, from_voice=from_voice,
            code_switch=code_switch, spirit_chat=spirit_chat,
            grammar_followup=grammar_followup, followup_target=followup_target,
        )
        window = list(history)[-settings.AI_HISTORY_MESSAGES:]
        if grammar_followup and followup_target and window and window[-1].role == 'user':
            raw = (window[-1].content or '').strip()
            note = (
                '[GRAMMAR FOLLOW-UP: explain the TARGET sentence from the system prompt '
                'in detail — not only this new meta-question.]\n'
            )
            if not raw.startswith('[GRAMMAR FOLLOW-UP'):
                window = [*window[:-1], ChatMessage('user', note + raw)]
        elif check_english and window and window[-1].role == 'user':
            raw = (window[-1].content or '').strip()
            if raw and not raw.startswith('[Grade the COMPLETE'):
                note = (
                    '[Grade the COMPLETE spoken English below — every clause, '
                    'not just the first part. Quote the full utterance in Услышал.]\n'
                )
                window = [*window[:-1], ChatMessage('user', note + raw)]
        messages = [system, *window]
        if spirit_chat:
            cap = 800
        elif grammar_followup:
            cap = 900
        elif check_english:
            cap = 700
        else:
            cap = 450
        max_tokens = min(settings.AI_MAX_OUTPUT_TOKENS, cap)

        try:
            chat = await self.provider.chat(
                messages,
                max_tokens=max_tokens,
                temperature=0.5,
            )
        except Exception:  # noqa: BLE001
            return (
                '🇷🇺 <b>По-русски:</b> не получилось ответить — попробуй ещё раз.\n'
                '🇬🇧 <b>English:</b> Sorry, could you repeat that?'
            )

        return chat.text


tutor = EnglishTutor()
