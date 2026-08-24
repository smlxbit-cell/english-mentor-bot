"""Merge usage examples into word-bank rows."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_OVERRIDES_PATH = (
    Path(__file__).resolve().parent.parent / 'data' / 'word_bank' / 'example_overrides.json'
)
_TEMPLATE_RE = re.compile(
    r'^I like .+[.!?]$|^This is .+[.!?]$|^It is about .+[.!?]$'
    r'|^I want .+[.!?]$|^I need the .+[.!?]$',
    re.I,
)
_BRITISH_RE = re.compile(
    r'\b(colou?r|favour|favourite|honour|centre|metre|organise|organised|'
    r'organising|realise|recognise|travelled|travelling|grey|defence|licence)\b',
    re.I,
)
_GARBAGE_RE = re.compile(
    r'\b(lorem|ipsum|xxx|asdf|something something)\b', re.I,
)


def _load_overrides() -> dict[str, dict[str, str]]:
    if not _OVERRIDES_PATH.is_file():
        return {}
    data = json.loads(_OVERRIDES_PATH.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for key, val in data.items():
        if not isinstance(val, dict):
            continue
        out[str(key).lower()] = {
            'example': str(val.get('example', '')).strip(),
            'example_ru': str(val.get('example_ru', '')).strip(),
        }
    return out


@lru_cache(maxsize=1)
def example_overrides() -> dict[str, dict[str, str]]:
    return _load_overrides()


def headword_in_example(example: str, headword: str) -> bool:
    if not example or not headword:
        return False
    return bool(re.search(rf'\b{re.escape(headword.strip())}\b', example, re.I))


def is_natural_american_example(example: str) -> bool:
    """Reject British spellings, filler junk, and textbook-only phrasing."""
    ex = (example or '').strip()
    if not ex:
        return False
    if _BRITISH_RE.search(ex):
        return False
    if _GARBAGE_RE.search(ex):
        return False
    if ex.count('"') >= 4:
        return False
    return True


def is_valid_context_example(
    word: dict,
    *,
    example: str = '',
    example_ru: str = '',
) -> bool:
    en = (word.get('english') or '').strip()
    ex = (example or word.get('example') or '').strip()
    ex_ru = (example_ru or word.get('example_ru') or '').strip()
    if not ex or not ex_ru or not en:
        return False
    if _TEMPLATE_RE.match(ex):
        return False
    if not is_natural_american_example(ex):
        return False
    if not headword_in_example(ex, en):
        return False
    min_words = 3 if (word.get('cefr_level') or '').lower() in ('a1', 'a2') else 4
    if len(ex.split()) < min_words:
        return False
    return True


def _pick_example_source(
    row: dict,
    *,
    override: dict[str, str] | None,
    tatoeba: dict[str, str] | None,
) -> dict[str, str] | None:
    from learning.word_bank.level_examples import load_level_examples

    if override and is_valid_context_example(
        row, example=override['example'], example_ru=override['example_ru'],
    ):
        return override
    level = (row.get('cefr_level') or '').lower()
    if level in ('a1', 'a2', 'b1', 'b2', 'c1'):
        cached = load_level_examples(level).get((row.get('english') or '').strip().lower())
        if cached and is_valid_context_example(row, example=cached['example'], example_ru=cached['example_ru']):
            return cached
    if is_valid_context_example(row):
        return {'example': row.get('example', ''), 'example_ru': row.get('example_ru', '')}
    if tatoeba and is_valid_context_example(
        row,
        example=tatoeba.get('example', ''),
        example_ru=tatoeba.get('example_ru', ''),
    ):
        return tatoeba
    return None


@lru_cache(maxsize=1)
def _tatoeba_lookup() -> dict[str, dict[str, str]]:
    try:
        from django.conf import settings
    except Exception:  # noqa: BLE001
        return {}
    path = (
        Path(settings.BASE_DIR) / 'learning' / 'data' / 'word_bank' / 'tatoeba_examples.json'
    )
    if not path.is_file():
        return {}
    from .tatoeba_loader import load_tatoeba_examples

    return load_tatoeba_examples(path)


def resolve_word_examples(row: dict) -> dict:
    """Best EN/RU usage examples for UI and drills (overrides → Tatoeba → stored)."""
    return enrich_row_examples(row, tatoeba_lookup=_tatoeba_lookup())


def enrich_row_examples(
    row: dict,
    *,
    tatoeba_lookup: dict[str, dict[str, str]] | None = None,
) -> dict:
    english = (row.get('english') or '').strip()
    if not english:
        return row
    key = english.lower()
    picked = _pick_example_source(
        row,
        override=example_overrides().get(key),
        tatoeba=(tatoeba_lookup or {}).get(key),
    )
    if picked:
        row = dict(row)
        row['example'] = picked['example']
        row['example_ru'] = picked['example_ru']
        return row
    row = dict(row)
    row['example'] = ''
    row['example_ru'] = ''
    return row


def enrich_rows_examples(
    rows: dict[str, dict],
    *,
    tatoeba_lookup: dict[str, dict[str, str]] | None = None,
) -> dict[str, dict]:
    return {
        slug: enrich_row_examples(row, tatoeba_lookup=tatoeba_lookup)
        for slug, row in rows.items()
    }
