"""Headword quality filters — conversational English, no medical/scientific junk."""

from __future__ import annotations

import re

# Medical / scientific EN patterns (headword or translation).
_MEDICAL_EN_SUFFIXES = re.compile(
    r'(itis|osis|emia|ology|ectomy|otomy|pathy|plasty|scopy|stomy|uria|'
    r'genic|cyte|phage|blast|trophy|rrhea|penia|plasia|lysis)$',
    re.I,
)
_MEDICAL_EN_PREFIXES = re.compile(
    r'^(hyper|hypo|neuro|cardio|gastro|hepato|osteo|psycho|immuno|micro|macro|'
    r'poly|mono|meta|pseudo|proto|electro|photo|radio|thermo|bio|chemo|'
    r'hemo|haemo|leuko|melan|oste|rhino|stomato|nephro|pulmo|viro|bacterio)',
    re.I,
)
_MEDICAL_RU = re.compile(
    r'(ит\b|оз\b|емия|еми\b|ология|эктомия|патия|скопия|синдром|'
    r'диагноз|хирург|анатом|патolog|абеталип|абелиан|акантоцеф|'
    r'абортивн|абстракционизм)',
    re.I,
)
_CONSONANT_RUN = re.compile(r'[^aeiou\-]{5,}', re.I)
# Conversational bank: no obscure 2-letter abbreviations (ab, ac, …).
_TWO_LETTER_ALLOW = frozenset({
    'ok', 'tv', 'pc', 'id', 'uk', 'us', 'eu', 'ai', 'it', 'pm', 'am',
})
# Latin-only 2–3 letter tokens that are abbreviations, not vocabulary.
_ABBREV_RE = re.compile(
    r'^(?:ab|ac|ad|bc|cf|eg|et|ex|ff|ib|id|ie|lb|oz|vs|viz|vol|yr'
    r'|adj|adv|fig|max|min|num|ref|syn)$',
    re.I,
)


def is_acceptable_headword(
    english: str,
    translation: str = '',
    *,
    part_of_speech: str = '',
    source: str = '',
    allow_curated: bool = False,
) -> bool:
    """Reject obscure medical/technical headwords unsuitable for conversation."""
    if allow_curated:
        return True
    en = (english or '').strip().lower()
    ru = (translation or '').strip()
    if not en or len(en) < 2:
        return False
    if len(en) == 2:
        if en not in _TWO_LETTER_ALLOW:
            return False
    if len(en) <= 3 and _ABBREV_RE.match(en):
        return False
    if not en.isalpha() and not en.replace('-', '').isalpha():
        return False
    if len(en) > 22:
        return False
    if en.count('-') > 2:
        return False
    if _CONSONANT_RUN.search(en.replace('-', '')):
        return False
    if _MEDICAL_EN_SUFFIXES.search(en.replace('-', '')):
        return False
    if _MEDICAL_EN_PREFIXES.search(en):
        return False
    if ru and _MEDICAL_RU.search(ru.lower()):
        return False
    pos = (part_of_speech or '').lower()
    if source in ('enru_supplement', 'freedict_supplement'):
        return bool((translation or '').strip())
    return True


def filter_row(row: dict, *, allow_curated: bool | None = None) -> bool:
    topics = row.get('topics') or []
    curated = allow_curated
    if curated is None:
        curated = 'remote' not in topics or any(
            t in topics for t in (
                'greetings', 'people', 'food', 'places', 'time',
                'education', 'work', 'travel', 'communication',
            )
        )
    return is_acceptable_headword(
        row.get('english', ''),
        row.get('translation', ''),
        part_of_speech=row.get('part_of_speech', ''),
        source=row.get('source', ''),
        allow_curated=curated,
    )
