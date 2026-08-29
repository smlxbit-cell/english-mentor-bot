"""Grammar rule categories — 5 sections per CEFR level (A1–C1)."""

from __future__ import annotations

# slug → (emoji, Russian label) — LOCKED navigation (max 5 per level)
CATEGORY_META: dict[str, tuple[str, str]] = {
    'phrases': ('👋', 'Фразы и общение'),
    'verbs': ('⚡', 'Глаголы и времена'),
    'words': ('📝', 'Местоимения и формы'),
    'links': ('🔗', 'Предлоги и связки'),
    'syntax': ('🧩', 'Предложение и вопросы'),
}

# Fine-grained bank topic → category slug
TOPIC_TO_CATEGORY: dict[str, str] = {
    # phrases
    'Приветствия': 'phrases',
    'Вежливые слова и фразы': 'phrases',
    'Отель': 'phrases',
    'Работа': 'phrases',
    'Общение': 'phrases',
    'Числа': 'phrases',
    'Время': 'phrases',
    # verbs
    'Глагол to be': 'verbs',
    'Present Simple': 'verbs',
    'Present Continuous': 'verbs',
    'Past Simple': 'verbs',
    'Past Continuous': 'verbs',
    'Present Perfect': 'verbs',
    'Past Perfect': 'verbs',
    'Future': 'verbs',
    'Модальные глаголы': 'verbs',
    'Пассивный залог': 'verbs',
    'Глагол have': 'verbs',
    'Инфинитив': 'verbs',
    'Фразовые глаголы': 'verbs',
    # words (nouns, articles, adjectives, pronouns)
    'Артикли': 'words',
    'Существительные': 'words',
    'Указатели': 'words',
    'Притяжательные': 'words',
    'Прилагательные': 'words',
    'Местоимения': 'words',
    'Количество': 'words',
    # links
    'Предлоги': 'links',
    'Союзы': 'links',
    'Связки': 'links',
    # syntax
    'Вопросы': 'syntax',
    'Навигация': 'syntax',
    'Порядок слов': 'syntax',
    'Условие': 'syntax',
    'Придаточные': 'syntax',
    'Косвенная речь': 'syntax',
    'Согласование': 'syntax',
}

LEVEL_CATEGORY_ORDER: dict[str, list[str]] = {
    'a1': ['words', 'phrases', 'verbs', 'links', 'syntax'],
    'a2': ['phrases', 'verbs', 'words', 'links', 'syntax'],
    'b1': ['verbs', 'syntax', 'phrases', 'words', 'links'],
    'b2': ['verbs', 'syntax', 'words', 'links', 'phrases'],
    'c1': ['syntax', 'verbs', 'phrases', 'words', 'links'],
}


def category_slug_for_topic(topic: str) -> str:
    return TOPIC_TO_CATEGORY.get((topic or '').strip(), 'syntax')


def category_label(slug: str) -> str:
    emoji, title = CATEGORY_META.get(slug, CATEGORY_META['syntax'])
    return f'{emoji} {title}'


def category_button_label(slug: str, count: int) -> str:
    emoji, title = CATEGORY_META.get(slug, CATEGORY_META['syntax'])
    short = title if len(title) <= 22 else f'{title[:21]}…'
    return f'{emoji} {short} · {count}'


def parse_rules_bank_page_cb(
    data: str, action: str,
) -> tuple[str, str | None, int] | tuple[str, str, int, int] | None:
    """Parse page train/learn callbacks with optional topic index."""
    prefix = f'rules:bank:page:{action}:'
    if not data.startswith(prefix):
        return None
    rest = data[len(prefix):]
    parts = rest.split(':')
    if len(parts) == 2:
        level, page_s = parts
        if not page_s.isdigit():
            return None
        return level, None, int(page_s)
    if len(parts) == 3:
        level, category, page_s = parts
        if not page_s.isdigit():
            return None
        return level, category, int(page_s)
    if len(parts) == 4:
        level, category, topic_idx_s, page_s = parts
        if not topic_idx_s.isdigit() or not page_s.isdigit():
            return None
        return level, category, int(topic_idx_s), int(page_s)
    return None


def parse_rules_topic_page_cb(data: str) -> tuple[str, str, int, int] | None:
    """Parse ``rules:bank:topic:{level}:{category}:{topic_idx}:{page}``."""
    prefix = 'rules:bank:topic:'
    if not data.startswith(prefix):
        return None
    parts = data[len(prefix):].split(':')
    if len(parts) != 4:
        return None
    level, category, topic_idx_s, page_s = parts
    if not topic_idx_s.isdigit() or not page_s.isdigit():
        return None
    return level, category, int(topic_idx_s), int(page_s)


def parse_rules_survey_page_cb(data: str) -> tuple[str, str | None, int] | None:
    """Parse ``rules:survey:page:{level}[:{category}]:{page}``."""
    prefix = 'rules:survey:page:'
    if not data.startswith(prefix):
        return None
    rest = data[len(prefix):]
    parts = rest.split(':')
    if len(parts) == 2:
        level, page_s = parts
        category = None
    elif len(parts) == 3:
        level, category, page_s = parts
    else:
        return None
    if not page_s.isdigit():
        return None
    return level, category, int(page_s)
