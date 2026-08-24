"""Per-level AI-generated example caches ({level}_examples.json)."""

from __future__ import annotations

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'word_bank'

EXAMPLES_PER_WORD = 3


def examples_path(level: str, *, data_dir: Path | None = None) -> Path:
    base = data_dir or _DATA_DIR
    return base / f'{level.lower()}_examples.json'


def _normalize_entry(raw: dict) -> dict:
    examples: list[dict[str, str]] = []
    if isinstance(raw.get('examples'), list):
        for item in raw['examples']:
            if not isinstance(item, dict):
                continue
            ex = str(item.get('example', '')).strip()
            ex_ru = str(item.get('example_ru', '')).strip()
            if ex and ex_ru:
                examples.append({'example': ex, 'example_ru': ex_ru})
    if not examples:
        ex = str(raw.get('example', '')).strip()
        ex_ru = str(raw.get('example_ru', '')).strip()
        if ex and ex_ru:
            examples.append({'example': ex, 'example_ru': ex_ru})
    primary = examples[0] if examples else {'example': '', 'example_ru': ''}
    return {
        'example': primary['example'],
        'example_ru': primary['example_ru'],
        'examples': examples[:EXAMPLES_PER_WORD],
    }


def load_level_examples(level: str, *, data_dir: Path | None = None) -> dict[str, dict]:
    path = examples_path(level, data_dir=data_dir)
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return {}
    return {
        str(k).lower(): _normalize_entry(v if isinstance(v, dict) else {})
        for k, v in data.items()
    }


def save_level_examples(
    level: str,
    lookup: dict[str, dict],
    *,
    data_dir: Path | None = None,
) -> Path:
    path = examples_path(level, data_dir=data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict] = {}
    for key, val in lookup.items():
        norm = _normalize_entry(val if isinstance(val, dict) else {})
        if norm['examples']:
            out[key] = norm
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def is_level_examples_cache_file(name: str) -> bool:
    low = name.lower()
    return low.endswith('_examples.json') and low not in {
        'tatoeba_examples.json',
        'example_overrides.json',
    }
