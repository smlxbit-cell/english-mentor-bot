"""Merge multiple EN→RU senses into a concise learner-facing translation string."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

MAX_TRANSLATION_PARTS = 4
_SPLIT_RE = re.compile(r'[,;/|]+')
_STRESS_RE = re.compile(r'[\u0301\u0300]')
_CYR_WORD_RE = re.compile(r'[а-яё\u0301]+', re.I)
_IPA_RE = re.compile(r'/[^/]*/')
_POS_RE = re.compile(r'\b(?:noun|verb|adjective|adverb|interjection|interj)\b', re.I)

_OVERRIDES_PATH = (
    Path(__file__).resolve().parent.parent / 'data' / 'word_bank' / 'translation_overrides.json'
)


def strip_stress(text: str) -> str:
    return _STRESS_RE.sub('', (text or '').strip())


def normalize_ru(text: str) -> str:
    return strip_stress(text).lower().replace('ё', 'е')


def split_translation_parts(text: str) -> list[str]:
    parts: list[str] = []
    seen: set[str] = set()
    for chunk in _SPLIT_RE.split(text or ''):
        word = strip_stress(chunk.strip())
        if not word:
            continue
        key = normalize_ru(word)
        if key in seen:
            continue
        seen.add(key)
        parts.append(word)
    return parts


def _load_overrides() -> dict[str, str]:
    if not _OVERRIDES_PATH.is_file():
        return {}
    data = json.loads(_OVERRIDES_PATH.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return {}
    return {str(k).lower(): str(v).strip() for k, v in data.items() if v}


@lru_cache(maxsize=1)
def translation_overrides() -> dict[str, str]:
    return _load_overrides()


def _is_loanword_match(english: str, russian: str) -> bool:
    en = (english or '').strip().lower()
    ru = normalize_ru(russian)
    if not en or not ru:
        return False
    if en == ru:
        return True
    if len(en) >= 3 and ru.startswith(en[: min(4, len(en))]):
        return True
    if en == 'chip' and ru == 'чип':
        return True
    return False


def _pos_bucket(part_of_speech: str) -> str:
    pos = (part_of_speech or '').lower().strip()
    if pos.startswith('n') or pos == 'phrase':
        return 'noun'
    if pos.startswith('v'):
        return 'verb'
    if pos.startswith('adj'):
        return 'adjective'
    if pos.startswith('adv'):
        return 'adverb'
    if pos.startswith('interj'):
        return 'interjection'
    return 'noun'


def _section_for_pos(text: str, part_of_speech: str) -> str:
    bucket = _pos_bucket(part_of_speech)
    parts = _POS_RE.split(text)
    if len(parts) <= 1:
        return text
    current = ''
    section = text
    for idx in range(1, len(parts), 2):
        label = parts[idx].lower()
        body = parts[idx + 1] if idx + 1 < len(parts) else ''
        if label == bucket:
            section = f'{label} {body}'
            break
        if not current and label == 'noun':
            current = f'{label} {body}'
    if bucket != 'noun' and section == text and current:
        return current
    return section


def _find_loanword(english: str, text: str) -> str:
    en = (english or '').strip().lower()
    if not en or not text:
        return ''
    for match in _CYR_WORD_RE.finditer(text):
        word = strip_stress(match.group(0))
        if _is_loanword_match(en, word):
            return word
    return ''


def extract_freedict_senses(
    text: str,
    *,
    max_senses: int = MAX_TRANSLATION_PARTS,
    part_of_speech: str = '',
) -> list[str]:
    """Pick one primary Russian gloss per sense block from WikDict/FreeDict text."""
    if not text:
        return []
    cleaned = _IPA_RE.sub(' ', text)
    cleaned = re.sub(r'\[\[[^\]]+\]\]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    section = _section_for_pos(cleaned, part_of_speech)

    chunks: list[str] = []
    for raw in re.split(r'\s+(?=\([a-z][^)]{0,60}\)\s*)', section):
        chunks.extend(part for part in re.split(r'\s+(?=A [a-z])', raw) if part.strip())
    if len(chunks) <= 1:
        chunks = [part for part in re.split(r'\s+(?=A [a-z])', section) if part.strip()]

    out: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        words = _CYR_WORD_RE.findall(chunk)
        if not words:
            continue
        primary = strip_stress(words[0])
        key = normalize_ru(primary)
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        out.append(primary)
        if len(out) >= max_senses:
            break
    return out


def merge_translation_parts(
    english: str,
    *sources: str,
    max_parts: int = MAX_TRANSLATION_PARTS,
) -> str:
    """Combine translation strings; dedupe; keep order; cap length."""
    en = (english or '').strip().lower()
    override = translation_overrides().get(en)
    if override:
        return ', '.join(split_translation_parts(override)[:max_parts])

    merged: list[str] = []
    seen: set[str] = set()
    loanword: str | None = None

    for source in sources:
        for part in split_translation_parts(source):
            key = normalize_ru(part)
            if key in seen:
                continue
            seen.add(key)
            if loanword is None and _is_loanword_match(en, part):
                loanword = part
                continue
            merged.append(part)

    if loanword:
        loan_key = normalize_ru(loanword)
        merged = [loanword] + [p for p in merged if normalize_ru(p) != loan_key]

    return ', '.join(merged[:max_parts])


def enrich_translation(
    english: str,
    primary: str,
    *,
    freedict_text: str = '',
    part_of_speech: str = '',
    max_parts: int = MAX_TRANSLATION_PARTS,
) -> str:
    primary_parts = split_translation_parts(primary)
    if translation_overrides().get((english or '').strip().lower()):
        return merge_translation_parts(english, primary, max_parts=max_parts)
    if len(primary_parts) >= 3:
        return primary.strip()

    loanword = _find_loanword(english, freedict_text)
    extra = extract_freedict_senses(
        freedict_text,
        max_senses=max_parts,
        part_of_speech=part_of_speech,
    )
    extra_text = ', '.join(extra)
    return merge_translation_parts(
        english, primary, extra_text, loanword, max_parts=max_parts,
    )


def enrich_row(row: dict, *, freedict_lookup: dict[str, str] | None = None) -> dict:
    english = (row.get('english') or '').strip()
    if not english:
        return row
    lookup = freedict_lookup or {}
    enriched = enrich_translation(
        english,
        row.get('translation') or '',
        freedict_text=lookup.get(english.lower(), ''),
        part_of_speech=row.get('part_of_speech') or '',
    )
    if enriched and enriched != row.get('translation'):
        row = dict(row)
        row['translation'] = enriched
    return row


def enrich_rows(
    rows: dict[str, dict],
    *,
    freedict_lookup: dict[str, str] | None = None,
) -> dict[str, dict]:
    lookup = freedict_lookup or {}
    return {
        slug: enrich_row(row, freedict_lookup=lookup)
        for slug, row in rows.items()
    }
