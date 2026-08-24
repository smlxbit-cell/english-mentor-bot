"""Consistent English (and related RU) capitalization for UI, lessons, and TTS."""

from __future__ import annotations

import re

# Lowercase key → canonical written form (proper nouns, languages, etc.).
ALWAYS_CAP: dict[str, str] = {
    'i': 'I',
    'english': 'English',
    'russian': 'Russian',
    'american': 'American',
    'british': 'British',
    'britain': 'Britain',
    'england': 'England',
    'scotland': 'Scotland',
    'wales': 'Wales',
    'ireland': 'Ireland',
    'uk': 'UK',
    'usa': 'USA',
    'us': 'US',
    'eu': 'EU',
    'london': 'London',
    'manchester': 'Manchester',
    'paris': 'Paris',
    'berlin': 'Berlin',
    'moscow': 'Moscow',
    'russia': 'Russia',
    'france': 'France',
    'germany': 'Germany',
    'china': 'China',
    'japan': 'Japan',
    'india': 'India',
    'spain': 'Spain',
    'italy': 'Italy',
    'europe': 'Europe',
    'asia': 'Asia',
    'africa': 'Africa',
    'america': 'America',
    'telegram': 'Telegram',
    'monday': 'Monday',
    'tuesday': 'Tuesday',
    'wednesday': 'Wednesday',
    'thursday': 'Thursday',
    'friday': 'Friday',
    'saturday': 'Saturday',
    'sunday': 'Sunday',
    'january': 'January',
    'february': 'February',
    'march': 'March',
    'april': 'April',
    'may': 'May',
    'june': 'June',
    'july': 'July',
    'august': 'August',
    'september': 'September',
    'october': 'October',
    'november': 'November',
    'december': 'December',
}

_PROPER_POS = frozenset({'proper noun', 'proper_noun', 'name', 'toponym'})


def _is_proper_part_of_speech(part_of_speech: str) -> bool:
    pos = (part_of_speech or '').strip().lower()
    if not pos:
        return False
    if pos in _PROPER_POS:
        return True
    return 'proper' in pos


def _cap_word_token(raw: str, *, sentence_start: bool) -> tuple[str, bool]:
    """Return (token, sentence_start_after)."""
    bare = re.sub(r"[^\w']", '', raw)
    low = bare.lower()
    if low in ALWAYS_CAP:
        fixed = ALWAYS_CAP[low]
        if bare:
            new = re.sub(re.escape(bare), fixed, raw, count=1, flags=re.I)
        else:
            new = fixed
        if raw.endswith(('.', '!', '?')):
            return new, True
        return new, False
    if sentence_start and bare:
        new = raw[:1].upper() + raw[1:] if len(raw) > 1 else raw.upper()
        if raw.endswith(('.', '!', '?')):
            return new, True
        return new, False
    if raw.endswith(('.', '!', '?')):
        return raw, True
    return raw, False


def format_english_text(text: str, *, headword: str = '') -> str:
    """Sentence caps + ALWAYS_CAP + optional headword form inside examples."""
    raw = (text or '').strip()
    if not raw:
        return ''
    hw = format_headword(headword) if headword else ''
    if hw and headword.strip():
        raw = re.sub(re.escape(headword.strip()), hw, raw, count=0, flags=re.I)
    words = raw.split()
    if not words:
        return raw
    out: list[str] = []
    sentence_start = True
    for token in words:
        new, sentence_start = _cap_word_token(token, sentence_start=sentence_start)
        out.append(new)
    return ' '.join(out)


def format_headword(english: str, *, part_of_speech: str = '') -> str:
    """Display form for a dictionary headword or short phrase."""
    raw = (english or '').strip()
    if not raw:
        return ''
    if _is_proper_part_of_speech(part_of_speech):
        return _title_phrase(raw)
    parts = raw.split()
    if len(parts) == 1:
        low = parts[0].lower()
        if low in ALWAYS_CAP:
            return ALWAYS_CAP[low]
        return parts[0]
    return format_english_text(raw)


def format_translation_display(
    translation: str,
    *,
    english: str = '',
    part_of_speech: str = '',
) -> str:
    """Capitalize Russian proper-name translations when the EN headword is proper."""
    tr = (translation or '').strip()
    if not tr:
        return tr
    if _is_proper_part_of_speech(part_of_speech) or (
        english.strip().lower() in ALWAYS_CAP
    ):
        if tr[0].islower():
            return tr[0].upper() + tr[1:]
    return tr


def _title_phrase(text: str) -> str:
    out = []
    for part in text.split():
        bare = re.sub(r"[^\w']", '', part)
        low = bare.lower()
        if low in ALWAYS_CAP:
            fixed = ALWAYS_CAP[low]
            out.append(re.sub(re.escape(bare), fixed, part, count=1, flags=re.I) if bare else fixed)
        elif bare:
            out.append(part[:1].upper() + part[1:] if len(part) > 1 else part.upper())
        else:
            out.append(part)
    return ' '.join(out)


def display_word_fields(
    *,
    english: str,
    translation: str = '',
    example: str = '',
    part_of_speech: str = '',
) -> dict[str, str]:
    """Return display-ready english / translation / example strings."""
    en = format_headword(english, part_of_speech=part_of_speech)
    tr = format_translation_display(
        translation, english=english, part_of_speech=part_of_speech,
    )
    ex = format_english_text(example, headword=english) if example else ''
    return {'english': en, 'translation': tr, 'example': ex}
