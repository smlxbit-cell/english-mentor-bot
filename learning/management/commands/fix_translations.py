"""Clean FreeDict-style blobs in WordBankEntry.translation fields."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from learning.models import WordBankEntry
from learning.word_bank.service import refresh_words_from_bank
from learning.word_bank.translation_enrich import sanitize_translation_for_display


class Command(BaseCommand):
    help = 'Normalize stored translations to concise Russian glosses'

    def handle(self, *args, **options):
        updated = 0
        for entry in WordBankEntry.objects.filter(is_active=True).iterator():
            clean = sanitize_translation_for_display(
                entry.translation,
                english=entry.english,
                part_of_speech=entry.part_of_speech or '',
            )
            if clean and clean != entry.translation:
                entry.translation = clean[:200]
                entry.save(update_fields=['translation', 'updated_at'])
                updated += 1
        synced = refresh_words_from_bank()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {updated} bank entries; synced {synced} learner Word rows',
            ),
        )
