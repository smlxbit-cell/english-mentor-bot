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

TOPIC_ALIASES: dict[str, str] = {
    'food and drink': 'food',
    'food_and_drink': 'food',
    'food and dri': 'food',
    'work and career': 'work',
    'work and car': 'work',
    'work_and_career': 'work',
    'studying': 'education',
    'study': 'education',
    'career': 'work',
    'everyday communication': 'communication',
    'movies and tv series': 'communication',
    'moving abroad': 'travel',
    'english exams': 'education',
    'personal growth and self-development': 'general',
}

PAGE_SIZE = 6
SKIP_TOPICS = frozenset({'remote'})


def canonical_topic(raw: str) -> str:
    slug = (raw or '').strip().lower().replace('-', ' ').replace('_', ' ')
    slug = ' '.join(slug.split())
    if slug in TOPIC_ALIASES:
        return TOPIC_ALIASES[slug]
    if slug in TOPIC_META:
        return slug
    underscored = slug.replace(' ', '_')
    if underscored in TOPIC_ALIASES:
        return TOPIC_ALIASES[underscored]
    if underscored in TOPIC_META:
        return underscored
    return underscored.replace(' ', '_') if slug else 'general'


def normalize_topics(raw: list | None) -> list[str]:
    out: list[str] = []
    for topic in raw or []:
        if not topic or topic in SKIP_TOPICS:
            continue
        slug = canonical_topic(topic)
        if slug not in out:
            out.append(slug)
    return out or ['general']


def topic_label(slug: str) -> str:
    canon = canonical_topic(slug)
    icon, title = TOPIC_META.get(canon, ('📁', canon.replace('_', ' ').title()))
    return f'{icon} {title}'


def topic_button_label(slug: str, count: int) -> str:
    canon = canonical_topic(slug)
    icon, title = TOPIC_META.get(canon, ('📁', canon.replace('_', ' ').title()))
    return f'{icon} {title} · {count}'


def parse_paged_callback(data: str, marker: str) -> tuple[str, int] | None:
    """Parse ``{marker}{topic}:{page}`` safely (topic may contain underscores)."""
    if not data.startswith(marker):
        return None
    rest = data[len(marker):]
    if ':' not in rest:
        return None
    topic, page_s = rest.rsplit(':', 1)
    if not page_s.isdigit():
        return None
    return topic, int(page_s)
