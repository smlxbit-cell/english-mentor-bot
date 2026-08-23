"""Heuristic topic tagging for word-bank entries."""

from __future__ import annotations

import re
from functools import lru_cache

from .navigation import TOPIC_META, canonical_topic

# English / Russian substring hints per canonical topic slug.
_TOPIC_HINTS: dict[str, tuple[str, ...]] = {
    'greetings': (
        'hello', 'hi ', ' hi', 'goodbye', 'bye', 'please', 'thank', 'sorry',
        'welcome', 'greet', 'привет', 'до свидания', 'спасибо', 'извини',
    ),
    'food': (
        'food', 'eat', 'drink', 'coffee', 'tea', 'water', 'bread', 'meal',
        'restaurant', 'kitchen', 'fruit', 'meat', 'sugar', 'salt', 'hungry',
        'breakfast', 'lunch', 'dinner', 'cook', 'recipe', 'wine', 'beer',
        'juice', 'rice', 'pizza', 'cake', 'cheese', 'egg', 'fish', 'chicken',
        'apple', 'banana', 'vegetable', 'snack', 'menu', 'waiter', 'café',
        'cafe', 'еда', 'пить', 'кофе', 'чай', 'вода', 'хлеб', 'ресторан',
    ),
    'travel': (
        'travel', 'trip', 'airport', 'plane', 'flight', 'hotel', 'ticket',
        'passport', 'luggage', 'train', 'bus', 'taxi', 'map', 'tourist',
        'journey', 'abroad', 'border', 'visa', 'booking', 'reservation',
        'путешеств', 'аэропорт', 'самол', 'отель', 'билет', 'паспорт',
    ),
    'work': (
        'work', 'job', 'office', 'meeting', 'boss', 'colleague', 'salary',
        'hire', 'career', 'employee', 'employer', 'deadline', 'project',
        'client', 'resume', 'interview', 'promotion', 'shift', 'workplace',
        'работ', 'офис', 'начальник', 'коллег', 'зарплат', 'карьер',
    ),
    'business': (
        'business', 'company', 'market', 'profit', 'contract', 'deal',
        'invest', 'finance', 'budget', 'invoice', 'startup', 'trade',
        'commerce', 'shareholder', 'revenue', 'бизнес', 'компани', 'рынок',
        'контракт', 'прибыл', 'инвест',
    ),
    'people': (
        'people', 'person', 'man', 'woman', 'child', 'family', 'mother',
        'father', 'brother', 'sister', 'friend', 'baby', 'parent', 'husband',
        'wife', 'human', 'crowd', 'люди', 'семь', 'мама', 'папа', 'ребён',
        'друг', 'женщин', 'мужчин',
    ),
    'education': (
        'school', 'study', 'student', 'teacher', 'learn', 'university',
        'college', 'class', 'lesson', 'exam', 'homework', 'degree', 'course',
        'textbook', 'lecture', 'education', 'учит', 'школ', 'студент',
        'университет', 'урок', 'экзамен',
    ),
    'places': (
        'home', 'house', 'room', 'door', 'street', 'city', 'town', 'village',
        'building', 'park', 'shop', 'store', 'bank', 'hospital', 'place',
        'address', 'floor', 'garden', 'bridge', 'dom', 'дом', 'комнат',
        'улиц', 'город', 'здан', 'магазин',
    ),
    'time': (
        'day', 'week', 'month', 'year', 'today', 'tomorrow', 'yesterday',
        'morning', 'evening', 'night', 'hour', 'minute', 'second', 'clock',
        'calendar', 'season', 'spring', 'summer', 'autumn', 'winter', 'time',
        'день', 'недел', 'месяц', 'год', 'сегодня', 'завтра', 'утро', 'вечер',
        'час', 'минут',
    ),
    'communication': (
        'speak', 'talk', 'say', 'tell', 'ask', 'answer', 'phone', 'email',
        'message', 'chat', 'call', 'conversation', 'discuss', 'explain',
        'argue', 'agree', 'letter', 'news', 'report', 'language', 'word',
        'говор', 'сказ', 'спрос', 'ответ', 'телефон', 'письм', 'сообщ',
    ),
}

_POS_TOPIC: dict[str, str] = {
    'interj': 'greetings',
}


@lru_cache(maxsize=1)
def _lexicon_from_seed() -> dict[str, list[str]]:
    from .curriculum_words import iter_curriculum_rows
    from .seed_words import iter_builtin_rows

    lex: dict[str, list[str]] = {}
    for row in (*iter_builtin_rows(), *iter_curriculum_rows()):
        topics = [canonical_topic(t) for t in (row.get('topics') or []) if t]
        if not topics:
            continue
        key = row['english'].strip().lower()
        lex[key] = topics
    return lex


def classify_word(
    english: str,
    translation: str = '',
    *,
    part_of_speech: str = '',
) -> list[str]:
    """Return 1–2 canonical topic slugs for a headword."""
    en = (english or '').strip().lower()
    if not en:
        return ['general']

    lex = _lexicon_from_seed()
    if en in lex:
        return lex[en][:2]

    hay = f'{en} {(translation or "").lower()}'
    matched: list[str] = []
    for topic, hints in _TOPIC_HINTS.items():
        if any(h in hay for h in hints):
            matched.append(topic)

    pos = (part_of_speech or '').strip().lower()
    if pos in _POS_TOPIC and _POS_TOPIC[pos] not in matched:
        matched.insert(0, _POS_TOPIC[pos])

    if not matched:
        return ['general']

    # Prefer specific topics over catch-all general; cap at 2.
    out: list[str] = []
    for topic in matched:
        if topic in TOPIC_META and topic not in out:
            out.append(topic)
        if len(out) >= 2:
            break
    return out or ['general']


def resolve_topics(
    raw: list | None,
    *,
    english: str,
    translation: str = '',
    part_of_speech: str = '',
) -> list[str]:
    """Canonical topics for DB storage."""
    from .navigation import SKIP_TOPICS

    raw_list = [t for t in (raw or []) if t]
    if raw_list and raw_list != ['remote']:
        canon: list[str] = []
        for topic in raw_list:
            if topic in SKIP_TOPICS:
                continue
            slug = canonical_topic(topic)
            if slug not in canon:
                canon.append(slug)
        if canon:
            return canon
    return classify_word(english, translation, part_of_speech=part_of_speech)


def topic_matches(entry_topics: list | None, topic: str) -> bool:
    """True if entry belongs to the requested canonical topic."""
    slug = canonical_topic(topic)
    if slug == 'general':
        return normalize_topics_for_match(entry_topics) == ['general']
    return slug in normalize_topics_for_match(entry_topics)


def normalize_topics_for_match(raw: list | None) -> list[str]:
    from .navigation import SKIP_TOPICS

    out: list[str] = []
    for topic in raw or []:
        if not topic or topic in SKIP_TOPICS:
            continue
        slug = canonical_topic(topic)
        if slug not in out:
            out.append(slug)
    return out or ['general']
