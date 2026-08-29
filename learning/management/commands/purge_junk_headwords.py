"""Deactivate word-bank entries that fail conversational headword quality rules."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from learning.models import WordBankEntry
from learning.word_bank.service import refresh_words_from_bank
from learning.word_bank.word_quality import is_acceptable_headword


class Command(BaseCommand):
    help = 'Deactivate junk abbreviations and non-conversational headwords in WordBankEntry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print matches without deactivating',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        removed: list[str] = []
        for entry in WordBankEntry.objects.filter(is_active=True).iterator():
            if is_acceptable_headword(
                entry.english,
                entry.translation,
                part_of_speech=entry.part_of_speech or '',
            ):
                continue
            removed.append(f'{entry.cefr_level}:{entry.english} — {entry.translation[:40]}')
            if not dry:
                entry.is_active = False
                entry.save(update_fields=['is_active', 'updated_at'])
        if dry:
            for line in removed[:40]:
                self.stdout.write(line)
            if len(removed) > 40:
                self.stdout.write(f'… and {len(removed) - 40} more')
            self.stdout.write(self.style.WARNING(f'Would deactivate {len(removed)} entries'))
            return
        synced = refresh_words_from_bank() if removed else 0
        self.stdout.write(
            self.style.SUCCESS(
                f'Deactivated {len(removed)} junk entries; synced {synced} Word rows',
            ),
        )
