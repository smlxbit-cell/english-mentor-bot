"""Topic labels and navigation helpers for word bank UI."""

from __future__ import annotations

TOPIC_META: dict[str, tuple[str, str]] = {
    'general': ('📚', 'Общие'),
    'food': ('🍽', 'Еда'),
    'travel': ('✈️', 'Путешествия'),
    'work': ('💼', 'Работа'),
    'people': ('👥', 'Люди'),
    'education': ('🎓', 'Учёба'),
    'places': ('🏠', 'Места'),
    'time': ('⏰', 'Время'),
    'communication': ('💬', 'Общение'),
    'business': ('📊', 'Бизнес'),
    'greetings': ('👋', 'Приветствия'),
}

PAGE_SIZE = 6
SKIP_TOPICS = frozenset({'remote'})


def normalize_topics(raw: list | None) -> list[str]:
    topics = [t for t in (raw or []) if t and t not in SKIP_TOPICS]
    return topics or ['general']


def topic_label(slug: str) -> str:
    icon, title = TOPIC_META.get(slug, ('📁', slug.replace('_', ' ').title()))
    return f'{icon} {title}'


def topic_button_label(slug: str, count: int) -> str:
    icon, title = TOPIC_META.get(slug, ('📁', slug[:12]))
    return f'{icon} {title} · {count}'
