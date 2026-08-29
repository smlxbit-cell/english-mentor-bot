"""Audit active WordBankEntry rows for quality issues."""

from __future__ import annotations

from collections import defaultdict

from django.core.management.base import BaseCommand

from learning.english_display import ALWAYS_CAP, display_word_fields, format_headword
from learning.models import WordBankEntry
from learning.word_bank.translation_enrich import (
    _translation_has_english_noise,
    sanitize_translation_for_display,
)
from learning.word_bank.word_quality import is_acceptable_headword


def _should_capitalize(en: str, pos: str) -> bool:
    low = (en or '').strip().lower()
    if not low or ' ' in low:
        return False
    if low in ALWAYS_CAP:
        return True
    pos_l = (pos or '').lower()
    return 'proper' in pos_l or pos_l in {'name', 'toponym'}


class Command(BaseCommand):
    help = 'Report quality issues in active word bank entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Deactivate junk headwords and normalize translations',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=30,
            help='Max sample lines per issue category (default 30)',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        limit = options['limit']
        issues: dict[str, list[str]] = defaultdict(list)
        counts: dict[str, int] = defaultdict(int)
        deactivated = 0
        translation_fixed = 0

        for entry in WordBankEntry.objects.filter(is_active=True).iterator():
            en = entry.english or ''
            ru = entry.translation or ''
            pos = entry.part_of_speech or ''
            level = entry.cefr_level or '?'
            label = f'{level}:{en} — {ru[:50]}'

            if not is_acceptable_headword(en, ru, part_of_speech=pos):
                counts['junk_headword'] += 1
                if len(issues['junk_headword']) < limit:
                    issues['junk_headword'].append(label)
                if fix:
                    entry.is_active = False
                    entry.save(update_fields=['is_active', 'updated_at'])
                    deactivated += 1
                continue

            if not ru.strip():
                counts['empty_translation'] += 1
                if len(issues['empty_translation']) < limit:
                    issues['empty_translation'].append(label)
                continue

            if _translation_has_english_noise(ru):
                counts['english_in_translation'] += 1
                if len(issues['english_in_translation']) < limit:
                    issues['english_in_translation'].append(label)

            clean = sanitize_translation_for_display(
                ru, english=en, part_of_speech=pos,
            )
            if clean and clean != ru:
                counts['translation_needs_clean'] += 1
                if len(issues['translation_needs_clean']) < limit:
                    issues['translation_needs_clean'].append(
                        f'{level}:{en} | {ru[:40]} → {clean[:40]}',
                    )
                if fix:
                    entry.translation = clean[:200]
                    entry.save(update_fields=['translation', 'updated_at'])
                    translation_fixed += 1

            if '(TR!)' in ru or '(tr!)' in ru.lower():
                counts['tr_marker_in_translation'] += 1
                if len(issues['tr_marker_in_translation']) < limit:
                    issues['tr_marker_in_translation'].append(label)

            if len(en.strip()) == 3 and en.isalpha() and en.islower():
                if not is_acceptable_headword(en, ru, part_of_speech=pos):
                    counts['three_letter_junk'] += 1
                    if len(issues['three_letter_junk']) < limit:
                        issues['three_letter_junk'].append(label)

            if _should_capitalize(en, pos):
                disp = display_word_fields(
                    english=en, translation=ru, part_of_speech=pos,
                )
                if disp['english'] != format_headword(en, part_of_speech=pos):
                    pass
                if en == en.lower() and disp['english'] != en:
                    counts['proper_noun_display'] += 1
                    if len(issues['proper_noun_display']) < limit:
                        issues['proper_noun_display'].append(
                            f'{level}:{en} → {disp["english"]} — {disp["translation"]}',
                        )
                elif ru and ru[0].islower() and disp['translation'] and disp['translation'][0].isupper():
                    counts['proper_noun_ru_cap'] += 1
                    if len(issues['proper_noun_ru_cap']) < limit:
                        issues['proper_noun_ru_cap'].append(
                            f'{level}:{en} — {ru} → {disp["translation"]}',
                        )

        total = WordBankEntry.objects.filter(is_active=True).count()
        self.stdout.write(f'Active entries: {total}')
        for key in sorted(counts.keys()):
            self.stdout.write(f'\n[{key}] count={counts[key]}')
            for line in issues.get(key, []):
                self.stdout.write(f'  {line}')

        if fix:
            from learning.word_bank.service import refresh_words_from_bank

            synced = refresh_words_from_bank()
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nFixed: deactivated={deactivated}, '
                    f'translations={translation_fixed}, synced={synced}',
                ),
            )
        elif any(counts.values()):
            self.stdout.write(
                self.style.WARNING(
                    '\nRe-run with --fix to deactivate junk and clean translations',
                ),
            )
        else:
            self.stdout.write(self.style.SUCCESS('\nNo issues found'))
