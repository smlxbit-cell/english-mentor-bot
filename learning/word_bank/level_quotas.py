"""Per-level word quotas — each CEFR band has its own non-overlapping word set."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

CEFR_LEVELS = ('a1', 'a2', 'b1', 'b2', 'c1')

# Exclusive targets: A1=500 words only at A1, not cumulative.
LEVEL_TARGETS: dict[str, int] = {
    'a1': 500,
    'a2': 1000,
    'b1': 2000,
    'b2': 4000,
    'c1': 8000,
}

KELLY_EN_URL = (
    'https://raw.githubusercontent.com/kotoshu/frequency-list-kelly/main/data/en.json'
)

_CURATED_TOPIC_MARKERS = frozenset({
    'greetings', 'people', 'food', 'places', 'time', 'education', 'work',
})


def load_kelly_ranks(*, url: str = KELLY_EN_URL) -> dict[str, int]:
    """English headword (lower) → Kelly frequency rank (lower = more common)."""
    req = urllib.request.Request(url, headers={'User-Agent': 'english-mentor-bot/1.0'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    full_list = data.get('full_list') if isinstance(data, dict) else None
    if not isinstance(full_list, list):
        return {}
    ranks: dict[str, int] = {}
    for item in full_list:
        if not isinstance(item, dict):
            continue
        word = (item.get('word') or '').strip().lower()
        rank = item.get('rank')
        if word and isinstance(rank, int):
            ranks[word] = rank
    return ranks


def _is_curated(row: dict[str, Any]) -> bool:
    topics = row.get('topics') or []
    if not isinstance(topics, list):
        return False
    if 'remote' not in topics:
        return True
    return any(t in _CURATED_TOPIC_MARKERS for t in topics)


def _has_examples(row: dict[str, Any]) -> bool:
    return bool((row.get('example') or '').strip() and (row.get('example_ru') or '').strip())


def _row_sort_key(row: dict[str, Any], kelly_ranks: dict[str, int]) -> tuple:
    en = (row.get('english') or '').lower()
    rank = row.get('kelly_rank')
    if not isinstance(rank, int):
        rank = kelly_ranks.get(en, 999_999)
    return (
        0 if _has_examples(row) else 1,
        0 if _is_curated(row) else 1,
        rank,
        en,
    )


def apply_level_quotas(
    rows: dict[str, dict[str, Any]],
    *,
    levels: tuple[str, ...] | None = None,
    kelly_ranks: dict[str, int] | None = None,
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    """
    Keep up to LEVEL_TARGETS words per level; return (kept rows, dropped slugs).

    Only levels listed in ``levels`` are trimmed; others pass through unchanged.
    """
    if kelly_ranks is None:
        kelly_ranks = load_kelly_ranks()

    active_levels = levels or CEFR_LEVELS
    by_level: dict[str, list[tuple[str, dict[str, Any]]]] = {lvl: [] for lvl in CEFR_LEVELS}
    other: dict[str, dict[str, Any]] = {}

    for slug, row in rows.items():
        lvl = (row.get('cefr_level') or 'a1').lower()
        if lvl in by_level:
            by_level[lvl].append((slug, row))
        else:
            other[slug] = row

    kept: dict[str, dict[str, Any]] = dict(other)
    dropped: set[str] = set()

    for lvl in CEFR_LEVELS:
        items = by_level.get(lvl) or []
        if lvl not in active_levels:
            for slug, row in items:
                kept[slug] = row
            continue

        target = LEVEL_TARGETS.get(lvl, len(items))
        sorted_items = sorted(
            items,
            key=lambda pair: _row_sort_key(pair[1], kelly_ranks),
        )
        for slug, row in sorted_items[:target]:
            kept[slug] = row
        for slug, _row in sorted_items[target:]:
            dropped.add(slug)

    return kept, dropped
