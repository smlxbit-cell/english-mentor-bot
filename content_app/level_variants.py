"""Resolve per-step level_variants and min_level filters for lesson flows."""

from __future__ import annotations

import copy

LEVEL_ORDER = ['a0', 'a1', 'a2', 'b1', 'b2', 'c1', 'c2']


def _norm(level: str) -> str:
    lv = (level or 'a2').lower()
    return lv if lv in LEVEL_ORDER else 'a2'


def _level_index(level: str) -> int:
    return LEVEL_ORDER.index(_norm(level))


def apply_level_variants(steps: list[dict], user_level: str) -> list[dict]:
    """Filter steps by min_level and merge the best matching level_variants block."""
    user_idx = _level_index(user_level)
    resolved: list[dict] = []

    for step in steps:
        step = copy.deepcopy(step)
        content = dict(step.get('content') or {})

        min_level = content.pop('min_level', None)
        if min_level and user_idx < _level_index(min_level):
            continue

        variants = content.pop('level_variants', None)
        if variants:
            best_patch = None
            best_idx = -1
            for lv, patch in variants.items():
                idx = _level_index(lv)
                if idx <= user_idx and idx > best_idx:
                    best_patch = patch
                    best_idx = idx
            if best_patch:
                content = {**content, **best_patch}

        step['content'] = content
        resolved.append(step)

    return resolved
