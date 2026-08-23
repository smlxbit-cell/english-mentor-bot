"""Merge and upsert word-bank rows from built-in corpus, curriculum, and data files."""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from learning.models import WordBankEntry
from learning.word_bank.curriculum_words import iter_curriculum_rows
from learning.word_bank.loader import load_directory
from learning.word_bank.seed_words import iter_builtin_rows
from learning.word_bank.topic_classifier import resolve_topics

REMOTE_CACHE = 'remote.json'


def collect_word_bank_rows(
    *,
    data_dir: Path | None = None,
    include_remote: bool = False,
    fetch_remote: bool = False,
) -> dict[str, dict]:
    """Return slug → row dict; later sources override earlier ones."""
    merged: dict[str, dict] = {}

    if fetch_remote:
        from learning.word_bank.fetch_remote import iter_remote_rows

        remote_rows = list(iter_remote_rows())
        if data_dir:
            data_dir.mkdir(parents=True, exist_ok=True)
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
    return merged


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
            help='Download Kelly CEFR + EN↔RU dictionary and cache as remote.json',
        )
        parser.add_argument(
            '--include-remote',
            action='store_true',
            help='Merge cached remote.json (offline) into the bank',
        )

    def handle(self, *args, **options):
        data_dir = options.get('data_dir') or ''
        if not data_dir:
            data_dir = Path(settings.BASE_DIR) / 'learning' / 'data' / 'word_bank'
        else:
            data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

        rows = collect_word_bank_rows(
            data_dir=data_dir,
            include_remote=options['include_remote'] or options['fetch'],
            fetch_remote=options['fetch'],
        )
        if options['dry_run']:
            by_level: dict[str, int] = {}
            for row in rows.values():
                by_level[row['cefr_level']] = by_level.get(row['cefr_level'], 0) + 1
            self.stdout.write(f'Would upsert {len(rows)} words')
            for level in ('a1', 'a2', 'b1', 'b2', 'c1'):
                self.stdout.write(f'  {level.upper()}: {by_level.get(level, 0)}')
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
