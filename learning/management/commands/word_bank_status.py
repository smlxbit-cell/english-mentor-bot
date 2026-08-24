"""Print word-bank progress for all CEFR levels."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Q

from learning.models import WordBankEntry
from learning.word_bank.level_quotas import LEVEL_TARGETS


class Command(BaseCommand):
    help = 'Show word counts and example coverage per CEFR level'

    def handle(self, *args, **options):
        lines = ['Word bank status', '']
        for lvl, target in LEVEL_TARGETS.items():
            qs = WordBankEntry.objects.filter(cefr_level=lvl, is_active=True)
            total = qs.count()
            with_ex = qs.exclude(Q(example='') | Q(example__isnull=True)).count()
            pct = (with_ex * 100 // total) if total else 0
            lines.append(
                f'{lvl.upper()}: {total}/{target} words · '
                f'{with_ex} examples ({pct}%)',
            )
        text = '\n'.join(lines)
        self.stdout.write(text)
