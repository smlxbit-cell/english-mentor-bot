"""Quality-checked supplemental rows beyond Kelly-native CEFR tags."""

from __future__ import annotations

from typing import Iterator

from .american_spelling import americanize_headword
from .fetch_remote import EN_RU_URL, _WORD_RE, load_en_ru_lookup, load_kelly_cefr
from .frequency_levels import frequency_rank, infer_cefr_from_frequency, load_google10k_ranks
from .normalize import word_slug
from .topic_classifier import resolve_topics
from .translation_enrich import enrich_translation, extract_freedict_senses, sanitize_translation_for_display
from .word_quality import filter_row


def _is_supplement_row(row: dict) -> bool:
    source = (row.get('source') or '').strip()
    if source.endswith('_supplement'):
        return True
    topics = row.get('topics') or []
    return any(str(t).endswith('_supplement') for t in topics)


def is_supplement_row(row: dict) -> bool:
    return _is_supplement_row(row)


def iter_enru_supplement_rows(
    *,
    kelly_words: set[str] | None = None,
    freedict_lookup: dict[str, str] | None = None,
    ranks: dict[str, int] | None = None,
) -> Iterator[dict]:
    """EN↔RU vocabulary words not in Kelly — level from Google 10k frequency."""
    kelly = kelly_words if kelly_words is not None else set(load_kelly_cefr().keys())
    enru = load_en_ru_lookup()
    freedict = freedict_lookup or {}
    freq = ranks if ranks is not None else load_google10k_ranks()

    for en, ru in enru.items():
        if en in kelly:
            continue
        if not _WORD_RE.match(en):
            continue
        pos = ''
        fd_text = freedict.get(en, '')
        if fd_text.lower().startswith('proper noun'):
            pos = 'proper noun'
        translation = sanitize_translation_for_display(
            enrich_translation(
                en,
                ru,
                freedict_text=fd_text,
                part_of_speech=pos,
            ),
            english=en,
            part_of_speech=pos,
        )
        if not translation:
            continue
        level = infer_cefr_from_frequency(en, ranks=freq)
        head = americanize_headword(en)
        row = {
            'slug': word_slug(head),
            'english': head,
            'translation': translation,
            'example': '',
            'example_ru': '',
            'cefr_level': level,
            'part_of_speech': pos,
            'kelly_rank': frequency_rank(en, ranks=freq),
            'source': 'enru_supplement',
            'topics': resolve_topics(
                ['enru_supplement'],
                english=head,
                translation=translation,
                part_of_speech=pos,
            ),
        }
        if filter_row(row):
            yield row


def iter_freedict_supplement_rows(
    *,
    kelly_words: set[str] | None = None,
    enru_words: set[str] | None = None,
    freedict_lookup: dict[str, str] | None = None,
    ranks: dict[str, int] | None = None,
) -> Iterator[dict]:
    """FreeDict headwords missing from Kelly/EN-RU — strict sense extraction."""
    if not freedict_lookup:
        return
    kelly = kelly_words if kelly_words is not None else set(load_kelly_cefr().keys())
    enru = enru_words if enru_words is not None else set(load_en_ru_lookup().keys())
    seen = kelly | enru
    freq = ranks if ranks is not None else load_google10k_ranks()

    for en, fd_text in freedict_lookup.items():
        if en in seen:
            continue
        if not _WORD_RE.match(en):
            continue
        pos = 'noun'
        if fd_text.lower().startswith('verb '):
            pos = 'verb'
        elif fd_text.lower().startswith('adjective '):
            pos = 'adjective'
        elif fd_text.lower().startswith('adverb '):
            pos = 'adverb'
        senses = extract_freedict_senses(fd_text, max_senses=4, part_of_speech=pos)
        if not senses:
            continue
        translation = ', '.join(senses[:4])
        translation = sanitize_translation_for_display(
            translation, english=en, part_of_speech=pos,
        )
        if not translation:
            continue
        level = infer_cefr_from_frequency(en, ranks=freq)
        head = americanize_headword(en)
        row = {
            'slug': word_slug(head),
            'english': head,
            'translation': translation,
            'example': '',
            'example_ru': '',
            'cefr_level': level,
            'part_of_speech': pos,
            'kelly_rank': frequency_rank(en, ranks=freq),
            'source': 'freedict_supplement',
            'topics': resolve_topics(
                ['freedict_supplement'],
                english=head,
                translation=translation,
                part_of_speech=pos,
            ),
        }
        if filter_row(row):
            yield row
