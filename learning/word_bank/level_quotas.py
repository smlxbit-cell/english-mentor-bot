"""Per-level word quotas — each CEFR band has its own non-overlapping word set."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

CEFR_LEVELS = ('a1', 'a2', 'b1', 'b2', 'c1')
LEVEL_INDEX = {level: idx for idx, level in enumerate(CEFR_LEVELS)}

# Exclusive targets: each level has its own word count (not cumulative).
LEVEL_TARGETS: dict[str, int] = {
    'a1': 500,
    'a2': 1000,
    'b1': 2000,
    'b2': 4000,
    'c1': 8000,
}

# When native Kelly pool is smaller than target, promote words from the next band.
_LEVEL_FILL_FROM: dict[str, str] = {
    'a2': 'b1',
    'b1': 'b2',
    'b2': 'c1',
}

KELLY_EN_URL = (
    'https://raw.githubusercontent.com/kotoshu/frequency-list-kelly/main/data/en.json'
)

_CURATED_TOPIC_MARKERS = frozenset({
    'greetings', 'people', 'food', 'places', 'time', 'education', 'work',
    'travel', 'communication',
})


def quota_levels_for_requested(levels: tuple[str, ...]) -> tuple[str, ...]:
    """Applying A2 quota also re-applies A1 so lower bands stay trimmed."""
    if not levels:
        return CEFR_LEVELS
    max_idx = max(LEVEL_INDEX[lvl] for lvl in levels if lvl in LEVEL_INDEX)
    return tuple(CEFR_LEVELS[: max_idx + 1])


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


def _promote_rows(
    *,
    target_level: str,
    need: int,
    donor_level: str,
    by_level: dict[str, list[tuple[str, dict[str, Any]]]],
    kelly_ranks: dict[str, int],
    reserved: set[str],
) -> list[tuple[str, dict[str, Any]]]:
    if need <= 0:
        return []
    donors = [
        (slug, dict(row))
        for slug, row in by_level.get(donor_level, [])
        if slug not in reserved
    ]
    donors.sort(key=lambda pair: _row_sort_key(pair[1], kelly_ranks))
    promoted: list[tuple[str, dict[str, Any]]] = []
    for slug, row in donors[:need]:
        row['cefr_level'] = target_level
        promoted.append((slug, row))
        reserved.add(slug)
    return promoted


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
    reserved: set[str] = set()

    # Keep native Kelly C1/B2 at their bands before lower levels promote them away.
    for lvl in ('c1', 'b2'):
        for slug, row in sorted(
            by_level.get(lvl) or [],
            key=lambda pair: _row_sort_key(pair[1], kelly_ranks),
        ):
            if slug in reserved:
                continue
            copy = dict(row)
            copy['cefr_level'] = lvl
            kept[slug] = copy
            reserved.add(slug)

    for lvl in CEFR_LEVELS:
        native = list(by_level.get(lvl) or [])
        if lvl not in active_levels:
            for slug, row in native:
                if slug not in reserved:
                    kept[slug] = row
                    reserved.add(slug)
            continue

        target = LEVEL_TARGETS.get(lvl, len(native))
        available = [(slug, row) for slug, row in native if slug not in reserved]
        pool = sorted(available, key=lambda pair: _row_sort_key(pair[1], kelly_ranks))
        if len(pool) < target:
            donor = _LEVEL_FILL_FROM.get(lvl)
            if donor:
                pool.extend(_promote_rows(
                    target_level=lvl,
                    need=target - len(pool),
                    donor_level=donor,
                    by_level=by_level,
                    kelly_ranks=kelly_ranks,
                    reserved=reserved,
                ))
                pool.sort(key=lambda pair: _row_sort_key(pair[1], kelly_ranks))

        for slug, row in pool[:target]:
            kept[slug] = row
            reserved.add(slug)
        for slug, _row in pool[target:]:
            dropped.add(slug)
        for slug, _row in native:
            if slug not in reserved:
                dropped.add(slug)

    return kept, dropped
