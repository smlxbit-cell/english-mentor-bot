"""Normalize dictionary keys for deduplication."""

from __future__ import annotations

import re


def word_slug(english: str) -> str:
    s = (english or '').lower().strip()
    s = re.sub(r'[^\w\s\-]', '', s, flags=re.UNICODE)
    s = re.sub(r'\s+', '-', s).strip('-')
    return s[:140] or 'word'
