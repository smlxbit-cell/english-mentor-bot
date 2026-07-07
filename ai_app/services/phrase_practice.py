"""Detect when the learner wants mini-exercises on a phrase from tutor chat."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ai_app.services.types import ChatMessage

_PRACTICE_MARKERS = (
    'practice this', 'practice the', 'drill this', 'train this',
    'exercise on', 'exercises on', 'gap fill', 'fill in the blank',
    'translate these', 'translate some', 'test me on',
    'interesting phrase', 'useful phrase', 'this phrase', 'that phrase',
    'потренировать', 'потренируй', 'упражнен', 'упражнения',
    'пропуск', 'вставь', 'переведи', 'перевод',
    'эту фразу', 'эта фраза', 'это предложение', 'по этой фразе',
    'закрепить', 'потренируем',
)


def is_phrase_practice_request(text: str) -> bool:
    low = (text or '').lower()
    return any(m in low for m in _PRACTICE_MARKERS)


def extract_practice_phrase(text: str, history: Sequence[ChatMessage]) -> str:
    """Best English phrase to drill — from quotes or last tutor suggestion."""
    for pattern in (
        r'«([^»]{5,180})»',
        r'"([^"]{5,180})"',
        r"'([^']{5,180})'",
    ):
        matches = re.findall(pattern, text or '')
        for m in matches:
            if re.search(r'[a-zA-Z]{3,}', m):
                return m.strip()

    for msg in reversed(list(history)[:-1] if history else []):
        if msg.role != 'assistant':
            continue
        plain = re.sub(r'<[^>]+>', '', msg.content or '')
        for pattern in (
            r'Ещё можно сказать:\s*«([^»]+)»',
            r'Лучше:\s*«([^»]+)»',
            r'✅\s*«([^»]+)»',
            r'English:\s*«([^»]+)»',
        ):
            m = re.search(pattern, plain, re.I)
            if m:
                return m.group(1).strip()
        for m in re.finditer(r'«([A-Za-z][^»]{4,})»', plain):
            return m.group(1).strip()

    return ''
