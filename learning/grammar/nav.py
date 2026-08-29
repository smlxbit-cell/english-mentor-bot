"""Russian labels for grammar rule navigation buttons."""

from __future__ import annotations

import re

from content_app.rules_bank import RULES_BANK

_CYR_RE = re.compile(r'[а-яА-ЯёЁ]')

_NAV_BY_KEY: dict[str, str] = {
    r['key']: r['nav_ru']
    for r in RULES_BANK
    if r.get('nav_ru')
}


def _cyrillic_ratio(text: str) -> float:
    if not text:
        return 0.0
    cyr = len(_CYR_RE.findall(text))
    return cyr / max(len(text), 1)


def rule_nav_label(*, key: str, title: str = '', topic: str = '') -> str:
    """Button label for rule lists — Russian first, English title stays on the card."""
    if key in _NAV_BY_KEY:
        return _NAV_BY_KEY[key]
    if title and _cyrillic_ratio(title) >= 0.25:
        return title
    if topic:
        return topic
    return title or key


CATEGORY_PAGE_HINTS: dict[str, str] = {
    'phrases': 'Приветствия, просьбы, числа, время, заказ в кафе…',
    'verbs': 'To be, can, there is, present simple, like/want…',
    'words': 'Личные и притяжательные местоимения, артикли, this/that…',
    'links': 'In / on / at и другие предлоги, связки…',
    'syntax': 'Вопросы, навигация, порядок слов…',
}
