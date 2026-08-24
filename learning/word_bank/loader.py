"""Load word-bank rows from JSON/CSV files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from learning.word_bank.level_examples import is_level_examples_cache_file

CEFR_LEVELS = frozenset({'a1', 'a2', 'b1', 'b2', 'c1'})


def parse_row(raw: dict) -> dict | None:
    english = (raw.get('english') or raw.get('en') or '').strip()
    translation = (raw.get('translation') or raw.get('ru') or '').strip()
    if not english or not translation:
        return None
    level = (raw.get('cefr_level') or raw.get('level') or 'a1').lower().strip()
    if level not in CEFR_LEVELS:
        level = 'a1'
    topics = raw.get('topics') or []
    if isinstance(topics, str):
        topics = [t.strip() for t in topics.split(',') if t.strip()]
    return {
        'slug': word_slug(english),
        'english': english,
        'translation': translation,
        'example': (raw.get('example') or raw.get('example_en') or '').strip(),
        'example_ru': (raw.get('example_ru') or '').strip(),
        'cefr_level': level,
        'part_of_speech': (raw.get('part_of_speech') or raw.get('pos') or '').strip(),
        'topics': topics,
    }


def load_json_file(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, dict) and 'words' in data:
        data = data['words']
    if not isinstance(data, list):
        raise ValueError(f'{path}: expected JSON array or {{"words": [...]}}')
    rows = []
    for item in data:
        if not isinstance(item, dict):
            continue
        parsed = parse_row(item)
        if parsed:
            rows.append(parsed)
    return rows


def load_csv_file(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        for item in reader:
            parsed = parse_row(item)
            if parsed:
                rows.append(parsed)
    return rows


def load_directory(data_dir: Path) -> list[dict]:
    """Load all *.json and *.csv from a directory."""
    by_slug: dict[str, dict] = {}
    for path in sorted(data_dir.glob('*')):
        if path.name.lower() in {
            'remote.json', 'freedict_ru.json', 'translation_overrides.json',
            'tatoeba_examples.json', 'example_overrides.json',
        } or is_level_examples_cache_file(path.name):
            continue
        if path.suffix.lower() == '.json':
            items = load_json_file(path)
        elif path.suffix.lower() == '.csv':
            items = load_csv_file(path)
        else:
            continue
        for item in items:
            by_slug[item['slug']] = item
    return list(by_slug.values())
