"""Micro-quiz for daily warmup — one MC question per fact/phrase."""

from __future__ import annotations

import hashlib
from datetime import date

from study_app.daily_facts import DAILY_FACTS


def _seed(user_id: int, day: date, salt: str = '') -> int:
    raw = f'{user_id}:{day.isoformat()}:{salt}'.encode()
    return int(hashlib.sha256(raw).hexdigest(), 16)


def _distractors(fact: dict, count: int = 3) -> list[str]:
    pool = [f['en'] for f in DAILY_FACTS if f['en'] != fact.get('en')]
    if len(pool) < count:
        pool.extend([
            'Practice makes progress.',
            'Small steps every day matter.',
            'Speaking aloud helps your brain learn faster.',
        ])
    start = _seed(0, date.today(), fact.get('en', '')) % max(1, len(pool) - count)
    return pool[start:start + count]


def build_quiz_for_fact(fact: dict, user_id: int, day: date) -> dict:
    """Return quiz payload stored on the warmup block."""
    correct_en = fact.get('fact_en', '').strip()
    correct_ru = fact.get('fact_ru', '').strip()
    kind = fact.get('kind', 'fact')

    if kind == 'phrase':
        question_ru = 'Какая английская фраза соответствует смыслу выше?'
    else:
        question_ru = 'Какая фраза по-английски передаёт главную мысль?'

    wrong = _distractors(fact)
    options = [{'text': correct_en, 'correct': True}]
    for text in wrong[:3]:
        options.append({'text': text, 'correct': False})

    # Shuffle deterministically per user/day
    idx = list(range(len(options)))
    seed = _seed(user_id, day, 'quiz')
    for i in range(len(idx) - 1, 0, -1):
        j = seed % (i + 1)
        seed //= (i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    shuffled = [options[i] for i in idx]
    correct_index = next(i for i, o in enumerate(shuffled) if o['correct'])

    return {
        'question_ru': question_ru,
        'options': [o['text'] for o in shuffled],
        'correct_index': correct_index,
        'hint_ru': correct_ru[:120],
    }
