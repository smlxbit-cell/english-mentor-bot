"""Per-level AI-generated example caches ({level}_examples.json)."""

from __future__ import annotations

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'word_bank'


def examples_path(level: str, *, data_dir: Path | None = None) -> Path:
    base = data_dir or _DATA_DIR
    return base / f'{level.lower()}_examples.json'


def load_level_examples(level: str, *, data_dir: Path | None = None) -> dict[str, dict[str, str]]:
    path = examples_path(level, data_dir=data_dir)
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return {}
    return {
        str(k).lower(): {
            'example': str(v.get('example', '')).strip(),
            'example_ru': str(v.get('example_ru', '')).strip(),
        }
        for k, v in data.items()
        if isinstance(v, dict)
    }


def save_level_examples(
    level: str,
    lookup: dict[str, dict[str, str]],
    *,
    data_dir: Path | None = None,
) -> Path:
    path = examples_path(level, data_dir=data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lookup, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def is_level_examples_cache_file(name: str) -> bool:
    low = name.lower()
    return low.endswith('_examples.json') and low not in {
        'tatoeba_examples.json',
        'example_overrides.json',
    }
