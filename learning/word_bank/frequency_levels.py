"""Map English headwords to CEFR bands via open frequency lists."""

from __future__ import annotations

import json
import urllib.request
from functools import lru_cache

GOOGLE_10K_URL = (
    'https://raw.githubusercontent.com/first20hours/google-10000-english/master/'
    'google-10000-english-no-swears.txt'
)

CEFR_LEVELS = ('a1', 'a2', 'b1', 'b2', 'c1')

# Rank bands tuned so Kelly-native + EN-RU supplement can fill ~5000 slots.
_RANK_BANDS: tuple[tuple[int, str], ...] = (
    (450, 'a1'),
    (900, 'a2'),
    (1800, 'b1'),
    (5500, 'b2'),
    (10_000, 'c1'),
)


@lru_cache(maxsize=1)
def load_google10k_ranks(*, url: str = GOOGLE_10K_URL) -> dict[str, int]:
    req = urllib.request.Request(url, headers={'User-Agent': 'english-mentor-bot/1.0'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        lines = resp.read().decode('utf-8').splitlines()
    return {
        word.strip().lower(): idx + 1
        for idx, word in enumerate(lines)
        if word.strip()
    }


def infer_cefr_from_frequency(
    english: str,
    *,
    ranks: dict[str, int] | None = None,
    default: str = 'c1',
) -> str:
    lookup = ranks if ranks is not None else load_google10k_ranks()
    rank = lookup.get((english or '').strip().lower(), 12_000)
    for ceiling, level in _RANK_BANDS:
        if rank <= ceiling:
            return level
    return default


def frequency_rank(
    english: str,
    *,
    ranks: dict[str, int] | None = None,
) -> int:
    lookup = ranks if ranks is not None else load_google10k_ranks()
    return lookup.get((english or '').strip().lower(), 12_000)
