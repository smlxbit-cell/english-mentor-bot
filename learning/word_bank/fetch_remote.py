"""Download and merge open EN corpora (Kelly CEFR + EN↔RU dictionary)."""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Iterator

from .normalize import word_slug
from .translation_enrich import enrich_translation
from .american_spelling import americanize_headword

KELLY_EN_URL = (
    'https://raw.githubusercontent.com/kotoshu/frequency-list-kelly/main/data/en.json'
)
EN_RU_URL = (
    'https://raw.githubusercontent.com/iuzhakov/English-Russian-vocabulary/master/words.json'
)
CEFR_LEVELS = frozenset({'a1', 'a2', 'b1', 'b2', 'c1'})
_WORD_RE = re.compile(r"^[a-z][a-z\-']{0,39}$", re.I)


def _fetch_json(url: str, timeout: int = 120) -> object:
    req = urllib.request.Request(url, headers={'User-Agent': 'english-mentor-bot/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def load_en_ru_lookup(*, url: str = EN_RU_URL) -> dict[str, str]:
    """English headword (lower) → Russian translation (first sense)."""
    data = _fetch_json(url)
    if not isinstance(data, list):
        raise ValueError('EN-RU vocabulary: expected JSON array')
    lookup: dict[str, str] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        en = (item.get('en') or item.get('english') or '').strip().lower()
        ru = (item.get('ru') or item.get('translation') or '').strip()
        if en and ru and en not in lookup:
            lookup[en] = ru
    return lookup


def load_kelly_cefr(*, url: str = KELLY_EN_URL) -> dict[str, dict[str, str]]:
    """English headword (lower) → {level, pos}."""
    data = _fetch_json(url)
    full_list = data.get('full_list') if isinstance(data, dict) else None
    if not isinstance(full_list, list):
        raise ValueError('Kelly EN: expected full_list array')
    levels: dict[str, dict[str, str]] = {}
    for item in full_list:
        if not isinstance(item, dict):
            continue
        word = (item.get('word') or '').strip().lower()
        level = (item.get('cefr') or '').lower().strip()
        pos = (item.get('pos') or '').strip()
        if not word or level not in CEFR_LEVELS:
            continue
        if not _WORD_RE.match(word):
            continue
        if pos.lower() in {'proper noun', 'abbreviation', 'symbol'}:
            continue
        prev = levels.get(word)
        if prev is None or _level_rank(level) < _level_rank(prev['level']):
            rank = item.get('rank')
            levels[word] = {
                'level': level,
                'pos': pos,
                'rank': rank if isinstance(rank, int) else 999_999,
            }
    return levels


def _level_rank(level: str) -> int:
    order = {'a1': 0, 'a2': 1, 'b1': 2, 'b2': 3, 'c1': 4}
    return order.get(level, 99)


def iter_remote_rows(
    *,
    max_rows: int | None = None,
    freedict_lookup: dict[str, str] | None = None,
) -> Iterator[dict]:
    """
    Merge Kelly CEFR tags with EN↔RU dictionary.
    Only rows with a Russian translation are yielded.
    """
    lookup = load_en_ru_lookup()
    kelly = load_kelly_cefr()
    freedict = freedict_lookup or {}
    count = 0
    from .topic_classifier import resolve_topics

    for en, meta in kelly.items():
        ru = lookup.get(en)
        if not ru:
            ru = (freedict.get(en) or '').strip()
        if not ru:
            continue
        level = meta['level']
        pos = meta.get('pos') or ''
        ru = enrich_translation(
            en,
            ru,
            freedict_text=freedict.get(en, ''),
            part_of_speech=pos,
        )
        en = americanize_headword(en)
        row = {
            'slug': word_slug(en),
            'english': en,
            'translation': ru,
            'example': '',
            'example_ru': '',
            'cefr_level': level,
            'part_of_speech': pos,
            'kelly_rank': meta.get('rank', 999_999),
            'topics': resolve_topics(
                ['remote'],
                english=en,
                translation=ru,
                part_of_speech=pos,
            ),
        }
        yield row
        count += 1
        if max_rows and count >= max_rows:
            break
