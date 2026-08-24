"""Print word-bank progress for all CEFR levels."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Q

from learning.models import WordBankEntry
from learning.word_bank.level_quotas import LEVEL_TARGETS


def _example_count(entry: WordBankEntry) -> int:
    n = 0
    if (entry.example or '').strip() and (entry.example_ru or '').strip():
        n = 1
    extras = entry.extra_examples or []
    if isinstance(extras, list):
        for item in extras:
            if isinstance(item, dict) and (item.get('example') or '').strip():
                if (item.get('example_ru') or '').strip():
                    n += 1
    return n


class Command(BaseCommand):
    help = 'Show word counts and example coverage per CEFR level'

    def handle(self, *args, **options):
        lines = ['Word bank status', '']
        for lvl, target in LEVEL_TARGETS.items():
            qs = WordBankEntry.objects.filter(cefr_level=lvl, is_active=True)
            total = qs.count()
            with_primary = qs.exclude(
                Q(example='') | Q(example__isnull=True)
                | Q(example_ru='') | Q(example_ru__isnull=True)
            ).count()
            multi = sum(1 for e in qs if _example_count(e) >= 2)
            pct = (with_primary * 100 // total) if total else 0
            multi_pct = (multi * 100 // total) if total else 0
            lines.append(
                f'{lvl.upper()}: {total}/{target} words · '
                f'{with_primary} with example ({pct}%) · '
                f'{multi} with 2+ ({multi_pct}%)',
            )
        text = '\n'.join(lines)
        self.stdout.write(text)
