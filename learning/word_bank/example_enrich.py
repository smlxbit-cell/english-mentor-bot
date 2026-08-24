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
    r'^I like .+[.!?]$|^This is .+[.!?]$|^It is about .+[.!?]$',
    re.I,
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
    if not headword_in_example(ex, en):
        return False
    if len(ex.split()) < 4:
        return False
    return True


def enrich_row_examples(
    row: dict,
    *,
    tatoeba_lookup: dict[str, dict[str, str]] | None = None,
) -> dict:
    english = (row.get('english') or '').strip()
    if not english:
        return row
    key = english.lower()
    override = example_overrides().get(key)
    tatoeba = (tatoeba_lookup or {}).get(key)
    current_ex = (row.get('example') or '').strip()
    current_ru = (row.get('example_ru') or '').strip()

    if override and is_valid_context_example(row, example=override['example'], example_ru=override['example_ru']):
        row = dict(row)
        row['example'] = override['example']
        row['example_ru'] = override['example_ru']
        return row

    if is_valid_context_example(row):
        return row

    if tatoeba and is_valid_context_example(
        row,
        example=tatoeba.get('example', ''),
        example_ru=tatoeba.get('example_ru', ''),
    ):
        row = dict(row)
        row['example'] = tatoeba['example']
        row['example_ru'] = tatoeba['example_ru']
        return row

    if current_ex and not current_ru:
        row = dict(row)
        row['example'] = ''
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
