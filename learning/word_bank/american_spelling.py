"""Map common British headwords to American English for the word bank."""

from __future__ import annotations

HEADWORD_TO_AMERICAN: dict[str, str] = {
    'centre': 'center',
    'colour': 'color',
    'colours': 'colors',
    'favour': 'favor',
    'favourite': 'favorite',
    'favourites': 'favorites',
    'honour': 'honor',
    'metre': 'meter',
    'metres': 'meters',
    'organise': 'organize',
    'organised': 'organized',
    'organising': 'organizing',
    'realise': 'realize',
    'recognised': 'recognized',
    'recognise': 'recognize',
    'grey': 'gray',
    'defence': 'defense',
    'licence': 'license',
    'behaviour': 'behavior',
    'analyse': 'analyze',
    'catalogue': 'catalog',
    'programme': 'program',
    'travelled': 'traveled',
    'travelling': 'traveling',
}


def americanize_headword(english: str) -> str:
    key = (english or '').strip().lower()
    if not key:
        return english
    mapped = HEADWORD_TO_AMERICAN.get(key)
    if not mapped:
        return english
    if english.isupper():
        return mapped.upper()
    if english[0].isupper():
        return mapped.capitalize()
    return mapped
