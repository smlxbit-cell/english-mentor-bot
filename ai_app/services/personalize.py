"""Hybrid personalization: generate a single adaptive practice exercise.

Curated lessons stay the backbone; this adds one extra, cheap, cached practice
item targeting a learner's weak skill (and optional topic). Economical:
cheap model, JSON output, cached per (level, skill, topic, bucket), budget-capped,
with a deterministic fallback bank when AI is unavailable / over budget.
"""

from __future__ import annotations

import json
import random
import re

from django.conf import settings

from . import economy
from .registry import get_provider
from .types import ChatMessage

_SYSTEM = (
    'You create ONE short English practice exercise for a Russian-speaking learner. '
    'Return STRICT JSON only, no prose. Schema: '
    '{"exercise_type":"multiple_choice"|"fill_gap",'
    '"prompt_ru":"инструкция по-русски",'
    '"question":"English question or sentence with ___ for a gap",'
    '"options":["opt1","opt2","opt3"],'  # [] for fill_gap
    '"correct":"the correct option or word",'
    '"explanation_ru":"короткое объяснение по-русски"}'
)

# Deterministic fallback exercises (no tokens) per skill.
_FALLBACK = {
    'grammar': [
        {'exercise_type': 'multiple_choice',
         'prompt': 'Выбери правильную форму:',
         'question': 'She ___ to work every day.',
         'options': ['go', 'goes', 'going'], 'correct': ['goes'],
         'explanation': 'В Present Simple к he/she/it добавляем -s.'},
        {'exercise_type': 'fill_gap',
         'prompt': 'Вставь глагол to be:',
         'question': 'They ___ my friends.',
         'options': [], 'correct': ['are'],
         'explanation': 'they → are.'},
    ],
    'vocabulary': [
        {'exercise_type': 'multiple_choice',
         'prompt': 'Выбери перевод слова «книга»:',
         'question': 'книга',
         'options': ['book', 'cook', 'look'], 'correct': ['book'],
         'explanation': 'книга = book.'},
    ],
    'default': [
        {'exercise_type': 'multiple_choice',
         'prompt': 'Как вежливо попросить?',
         'question': 'How do you politely ask for water?',
         'options': ['Water!', 'Can I have some water, please?', 'Give water.'],
         'correct': ['Can I have some water, please?'],
         'explanation': 'Can I have …, please? — вежливая просьба.'},
    ],
}


def _fallback(skill: str) -> dict:
    bank = _FALLBACK.get(skill) or _FALLBACK['default']
    item = dict(random.choice(bank))
    item['skill'] = skill
    item['source'] = 'fallback'
    return item


def _parse(text: str, skill: str) -> dict | None:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r'\{.*\}', text or '', re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    etype = data.get('exercise_type', 'multiple_choice')
    correct = data.get('correct', '')
    if not correct:
        return None
    prompt_ru = str(data.get('prompt_ru', '')).strip()
    question = str(data.get('question', '')).strip()
    prompt = (prompt_ru + ('\n\n' + question if question else '')).strip()
    return {
        'exercise_type': 'fill_gap' if etype == 'fill_gap' else 'multiple_choice',
        'prompt': prompt or 'Задание:',
        'options': [str(o) for o in (data.get('options') or [])],
        'correct': [str(correct)],
        'explanation': str(data.get('explanation_ru', '')).strip(),
        'skill': skill,
        'source': 'ai',
    }


async def generate_practice(*, level: str, skill: str, topic: str = '',
                            user_key: str | None = None) -> dict:
    """Return one practice exercise dict for the given level/skill/topic."""
    skill = skill or 'grammar'
    bucket = random.randint(0, 4)  # cache up to 5 variants, then reuse
    key = economy.cache_key('practice', level, skill, topic, str(bucket))

    cached = economy.get_cached(key)
    if cached is not None:
        return cached

    if not economy.can_spend(user_key):
        return _fallback(skill)

    topic_hint = f' Topic/context: {topic}.' if topic else ''
    user_msg = (
        f'CEFR level: {level.upper()}. Skill focus: {skill}.{topic_hint} '
        'Make it slightly challenging but fair for this level. '
        'For multiple_choice give exactly 3 options with one correct.'
    )
    messages = [ChatMessage('system', _SYSTEM), ChatMessage('user', user_msg)]

    try:
        chat = await get_provider().chat(
            messages,
            model=settings.OPENAI_CHEAP_MODEL,
            max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
            temperature=0.7,
            json_mode=True,
        )
    except Exception:  # noqa: BLE001
        return _fallback(skill)

    economy.register_spend(user_key)
    parsed = _parse(chat.text, skill)
    if not parsed:
        return _fallback(skill)
    economy.set_cached(key, parsed)
    return parsed
