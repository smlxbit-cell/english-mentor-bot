"""Merge and upsert word-bank rows from built-in corpus, curriculum, and data files."""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from learning.models import WordBankEntry
from learning.word_bank.curriculum_words import iter_curriculum_rows
from learning.word_bank.example_enrich import enrich_rows_examples
from learning.word_bank.freedict_loader import CACHE_FILENAME as FREEDICT_CACHE
from learning.word_bank.freedict_loader import cache_freedict_lookup, load_freedict_lookup
from learning.word_bank.loader import load_directory
from learning.word_bank.seed_words import iter_builtin_rows
from learning.word_bank.tatoeba_loader import CACHE_FILENAME as TATOEBA_CACHE
from learning.word_bank.tatoeba_loader import cache_tatoeba_examples, load_tatoeba_examples
from learning.word_bank.level_quotas import (
    CEFR_LEVELS,
    LEVEL_TARGETS,
    apply_level_quotas,
    quota_levels_for_requested,
)
from learning.word_bank.topic_classifier import resolve_topics
from learning.word_bank.translation_enrich import enrich_rows

REMOTE_CACHE = 'remote.json'


def collect_word_bank_rows(
    *,
    data_dir: Path | None = None,
    include_remote: bool = False,
    fetch_remote: bool = False,
    fetch_freedict: bool = False,
    fetch_tatoeba: bool = False,
    quota_levels: tuple[str, ...] | None = None,
    tatoeba_headwords: list[str] | None = None,
    tatoeba_levels: tuple[str, ...] | None = None,
) -> tuple[dict[str, dict], set[str]]:
    """Return slug → row dict; later sources override earlier ones."""
    merged: dict[str, dict] = {}
    freedict_lookup: dict[str, str] = {}
    tatoeba_lookup: dict[str, dict[str, str]] = {}

    if data_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
        freedict_path = data_dir / FREEDICT_CACHE
        tatoeba_path = data_dir / TATOEBA_CACHE
        if fetch_freedict or fetch_remote:
            freedict_lookup = cache_freedict_lookup(freedict_path)
        elif freedict_path.is_file():
            freedict_lookup = load_freedict_lookup(freedict_path)
        if tatoeba_path.is_file():
            tatoeba_lookup = load_tatoeba_examples(tatoeba_path)

    if fetch_remote:
        from learning.word_bank.fetch_remote import iter_remote_rows

        remote_rows = list(iter_remote_rows(freedict_lookup=freedict_lookup))
        if data_dir:
            cache_path = data_dir / REMOTE_CACHE
            cache_path.write_text(
                json.dumps(remote_rows, ensure_ascii=False, indent=0),
                encoding='utf-8',
            )
        for row in remote_rows:
            merged[row['slug']] = row
    elif include_remote and data_dir:
        cache_path = data_dir / REMOTE_CACHE
        if cache_path.is_file():
            for row in json.loads(cache_path.read_text(encoding='utf-8')):
                merged[row['slug']] = row

    for row in iter_builtin_rows():
        merged[row['slug']] = row
    for row in iter_curriculum_rows():
        merged[row['slug']] = row
    if data_dir and data_dir.is_dir():
        for row in load_directory(data_dir):
            merged[row['slug']] = row

    if freedict_lookup:
        from learning.word_bank.fetch_remote import iter_freedict_supplement_rows

        for row in iter_freedict_supplement_rows(
            freedict_lookup,
            existing_slugs=set(merged.keys()),
        ):
            merged[row['slug']] = row

    merged = enrich_rows(merged, freedict_lookup=freedict_lookup)

    dropped_slugs: set[str] = set()
    if quota_levels:
        merged, dropped_slugs = apply_level_quotas(merged, levels=quota_levels)

    merged = _americanize_merged_rows(merged)

    if fetch_tatoeba and data_dir:
        if tatoeba_headwords is None:
            if tatoeba_levels:
                tatoeba_headwords = [
                    row['english']
                    for row in merged.values()
                    if row.get('cefr_level') in tatoeba_levels
                ]
            else:
                tatoeba_headwords = [row['english'] for row in merged.values()]
        cache_path = data_dir / TATOEBA_CACHE
        new_lookup = cache_tatoeba_examples(
            cache_path,
            headwords=tatoeba_headwords,
            merge_existing=True,
        )
        tatoeba_lookup = {**tatoeba_lookup, **new_lookup}
    merged = enrich_rows_examples(merged, tatoeba_lookup=tatoeba_lookup)
    return merged, dropped_slugs


def _americanize_merged_rows(rows: dict[str, dict]) -> dict[str, dict]:
    """Re-key rows when British headwords map to American spellings."""
    from learning.word_bank.american_spelling import americanize_headword
    from learning.word_bank.normalize import word_slug

    out: dict[str, dict] = {}
    for row in rows.values():
        en = americanize_headword(row.get('english') or '')
        row = dict(row)
        row['english'] = en
        row['slug'] = word_slug(en)
        out[row['slug']] = row
    return out


class Command(BaseCommand):
    help = 'Seed or update A1–C1 reference word bank (built-in + curriculum + data files)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default='',
            help='Directory with extra *.json / *.csv (default: learning/data/word_bank)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Count rows without writing to the database',
        )
        parser.add_argument(
            '--fetch',
            action='store_true',
            help='Download Kelly CEFR + EN↔RU dictionary + FreeDict and cache locally',
        )
        parser.add_argument(
            '--fetch-freedict',
            action='store_true',
            help='Download FreeDict eng-rus only (cached as freedict_ru.json)',
        )
        parser.add_argument(
            '--fetch-tatoeba',
            action='store_true',
            help='Download Tatoeba EN↔RU examples and cache as tatoeba_examples.json',
        )
        parser.add_argument(
            '--include-remote',
            action='store_true',
            help='Merge cached remote.json (offline) into the bank',
        )
        parser.add_argument(
            '--apply-quotas',
            action='store_true',
            help='Trim each level to LEVEL_TARGETS (use with --level to limit bands)',
        )
        parser.add_argument(
            '--level',
            action='append',
            choices=CEFR_LEVELS,
            dest='levels',
            help='Limit quota/Tatoeba to these CEFR bands (repeatable)',
        )

    def handle(self, *args, **options):
        data_dir = options.get('data_dir') or ''
        if not data_dir:
            data_dir = Path(settings.BASE_DIR) / 'learning' / 'data' / 'word_bank'
        else:
            data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

        quota_levels: tuple[str, ...] | None = None
        if options['apply_quotas']:
            if options['levels']:
                quota_levels = quota_levels_for_requested(tuple(options['levels']))
            else:
                quota_levels = CEFR_LEVELS

        rows, dropped_slugs = collect_word_bank_rows(
            data_dir=data_dir,
            include_remote=options['include_remote'] or options['fetch'],
            fetch_remote=options['fetch'],
            fetch_freedict=options['fetch_freedict'] or options['fetch'],
            fetch_tatoeba=options['fetch_tatoeba'],
            quota_levels=quota_levels,
            tatoeba_levels=tuple(options['levels']) if options['levels'] else None,
        )
        if options['dry_run']:
            by_level: dict[str, int] = {}
            ex_by_level: dict[str, int] = {}
            for row in rows.values():
                lvl = row['cefr_level']
                by_level[lvl] = by_level.get(lvl, 0) + 1
                if row.get('example') and row.get('example_ru'):
                    ex_by_level[lvl] = ex_by_level.get(lvl, 0) + 1
            self.stdout.write(f'Would upsert {len(rows)} words (drop {len(dropped_slugs)})')
            for level in CEFR_LEVELS:
                target = LEVEL_TARGETS.get(level, 0)
                count = by_level.get(level, 0)
                ex = ex_by_level.get(level, 0)
                self.stdout.write(
                    f'  {level.upper()}: {count}/{target} words, {ex} with examples',
                )
            return

        created = updated = 0
        for row in rows.values():
            topics = resolve_topics(
                row.get('topics'),
                english=row['english'],
                translation=row['translation'],
                part_of_speech=row.get('part_of_speech', ''),
            )
            _, was_created = WordBankEntry.objects.update_or_create(
                slug=row['slug'],
                defaults={
                    'english': row['english'],
                    'translation': row['translation'],
                    'example': row.get('example', ''),
                    'example_ru': row.get('example_ru', ''),
                    'cefr_level': row['cefr_level'],
                    'part_of_speech': row.get('part_of_speech', ''),
                    'topics': topics,
                    'is_active': True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Word bank: {created} created, {updated} updated ({len(rows)} total slugs)',
            ),
        )
        if dropped_slugs:
            n = WordBankEntry.objects.filter(slug__in=dropped_slugs, is_active=True).update(
                is_active=False,
            )
            self.stdout.write(f'Deactivated {n} words over level quota')

        from learning.word_bank.american_spelling import HEADWORD_TO_AMERICAN

        n_brit = WordBankEntry.objects.filter(
            english__in=list(HEADWORD_TO_AMERICAN.keys()),
            is_active=True,
        ).update(is_active=False)
        if n_brit:
            self.stdout.write(f'Deactivated {n_brit} British-spelling duplicates')

        from learning.word_bank.service import refresh_words_from_bank

        synced = refresh_words_from_bank()
        self.stdout.write(
            self.style.SUCCESS(f'Learner words synced from bank: {synced}'),
        )

        if quota_levels:
            for level in quota_levels:
                target = LEVEL_TARGETS.get(level, 0)
                active = WordBankEntry.objects.filter(is_active=True, cefr_level=level).count()
                with_ex = WordBankEntry.objects.filter(
                    is_active=True,
                    cefr_level=level,
                ).exclude(example='').exclude(example_ru='').count()
                self.stdout.write(
                    f'  {level.upper()}: {active}/{target} active, {with_ex} with examples',
                )
