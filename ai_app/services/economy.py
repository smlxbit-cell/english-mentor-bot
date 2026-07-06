"""Token-economy guardrails: per-user daily AI budget and a result cache.

Uses Django's default cache (LocMemCache). The bot runs as a single polling
process, so a per-process cache is sufficient for the prototype. Swap in Redis
later by configuring CACHES.
"""

from __future__ import annotations

import hashlib
from datetime import date

from django.conf import settings
from django.core.cache import cache

_BUDGET_TTL = 60 * 60 * 26  # a bit over a day
_CACHE_TTL = 60 * 60 * 24 * 7  # a week


def _today_key(user_key: str) -> str:
    return f'ai:budget:{user_key}:{date.today().isoformat()}'


def remaining_budget(user_key: str) -> int:
    limit = settings.AI_DAILY_CALL_LIMIT_PER_USER
    used = cache.get(_today_key(user_key), 0)
    return max(0, limit - used)


def can_spend(user_key: str | None) -> bool:
    if not user_key:
        return True
    return remaining_budget(user_key) > 0


def register_spend(user_key: str | None, amount: int = 1) -> None:
    if not user_key:
        return
    key = _today_key(user_key)
    try:
        cache.incr(key, amount)
    except ValueError:
        cache.set(key, amount, _BUDGET_TTL)


def cache_key(*parts: str) -> str:
    raw = '||'.join(parts)
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]
    return f'ai:check:{digest}'


def get_cached(key: str):
    return cache.get(key)


def set_cached(key: str, value) -> None:
    cache.set(key, value, _CACHE_TTL)
