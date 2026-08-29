"""Spirit rule card images — convention: media/spirit/rules/{rule_key}.{png|jpg|jpeg|webp}."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

_CARD_DIR = Path(settings.MEDIA_ROOT) / 'spirit' / 'rules'
_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')


def rule_card_relative_path(rule_key: str) -> str | None:
    """Relative path under MEDIA_ROOT, or None if no card uploaded yet."""
    key = (rule_key or '').strip().lower()
    if not key:
        return None
    for ext in _EXTENSIONS:
        rel = f'spirit/rules/{key}{ext}'
        if (_CARD_DIR / f'{key}{ext}').is_file():
            return rel
    return None


def rule_card_absolute_path(rule_key: str) -> Path | None:
    rel = rule_card_relative_path(rule_key)
    if not rel:
        return None
    return Path(settings.MEDIA_ROOT) / rel
