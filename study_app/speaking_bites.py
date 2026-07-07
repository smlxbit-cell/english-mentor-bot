"""Short speaking prompts for daily plans when speaking is a focus skill."""

from __future__ import annotations

import hashlib
from datetime import date

SPEAKING_BITES: list[dict] = [
    {
        'title': 'Introduce yourself',
        'prompt_ru': 'Представься: имя, откуда ты, чем занимаешься.',
        'prompt_en': 'My name is … I am from … I work as …',
        'model_answer': 'My name is Maria. I am from Russia. I work in online retail.',
        'keywords': ['name', 'from', 'work'],
        'minutes': 4,
    },
    {
        'title': 'Your day',
        'prompt_ru': 'Расскажи, как прошёл твой день (2–3 предложения).',
        'prompt_en': 'Today I … Then I …',
        'model_answer': 'Today I studied English. Then I had coffee with a friend.',
        'keywords': ['today', 'i'],
        'minutes': 4,
    },
    {
        'title': 'Ask for help',
        'prompt_ru': 'Попроси помощи в магазине или кафе.',
        'prompt_en': 'Excuse me, could you help me with …?',
        'model_answer': 'Excuse me, could you help me find this item, please?',
        'keywords': ['excuse', 'help', 'please'],
        'minutes': 4,
    },
]


def pick_speaking_bite(user_id: int, day: date) -> dict:
    raw = f'{user_id}:{day.isoformat()}:speak'.encode()
    idx = int(hashlib.sha256(raw).hexdigest(), 16) % len(SPEAKING_BITES)
    return SPEAKING_BITES[idx]
