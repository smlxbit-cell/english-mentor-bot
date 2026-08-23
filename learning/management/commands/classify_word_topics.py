"""Re-tag word-bank entries with canonical topics (fixes remote → general dump)."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from learning.models import WordBankEntry
from learning.word_bank.navigation import normalize_topics
from learning.word_bank.topic_classifier import classify_word, resolve_topics


class Command(BaseCommand):
    help = 'Reclassify word-bank topics (remote / general → themed groups)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print stats without updating rows',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        updated = 0
        by_topic: dict[str, int] = {}

        for entry in WordBankEntry.objects.filter(is_active=True).iterator():
            raw = entry.topics or []
            if (
                not raw
                or raw == ['remote']
                or 'remote' in raw
                or normalize_topics(raw) == ['general']
            ):
                new_topics = classify_word(
                    entry.english,
                    entry.translation,
                    part_of_speech=entry.part_of_speech,
                )
            else:
                new_topics = resolve_topics(
                    raw,
                    english=entry.english,
                    translation=entry.translation,
                    part_of_speech=entry.part_of_speech,
                )

            for topic in new_topics:
                by_topic[topic] = by_topic.get(topic, 0) + 1

            if new_topics != list(entry.topics or []):
                updated += 1
                if not dry:
                    entry.topics = new_topics
                    entry.save(update_fields=['topics'])

        self.stdout.write(f'Entries scanned: {WordBankEntry.objects.filter(is_active=True).count()}')
        self.stdout.write(f'Would update: {updated}' if dry else f'Updated: {updated}')
        for topic in sorted(by_topic, key=lambda t: (-by_topic[t], t)):
            self.stdout.write(f'  {topic}: {by_topic[topic]}')
