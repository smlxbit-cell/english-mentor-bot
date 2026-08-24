"""Generate missing usage examples for a CEFR level via AI (American EN + RU)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from learning.models import WordBankEntry
from learning.word_bank.example_enrich import enrich_row_examples, is_valid_context_example
from learning.word_bank.level_examples import load_level_examples, save_level_examples
from learning.word_bank.level_quotas import CEFR_LEVELS

BATCH_SIZE = 15

_LEVEL_PROMPT = {
    'a1': 'A1 (beginner)',
    'a2': 'A2 (elementary)',
    'b1': 'B1 (intermediate)',
    'b2': 'B2 (upper-intermediate)',
    'c1': 'C1 (advanced)',
}


async def _generate_batch(batch: list[dict], *, level: str) -> dict[str, dict[str, str]]:
    from ai_app.services.registry import get_provider
    from ai_app.services.types import ChatMessage

    level_label = _LEVEL_PROMPT.get(level, level.upper())
    items = [
        {
            'word': row['english'],
            'translation': row['translation'],
            'pos': row.get('part_of_speech') or '',
        }
        for row in batch
    ]
    prompt = (
        f'For each English headword, write ONE natural American English sentence ({level_label}) '
        'that uses the word correctly, plus an accurate Russian translation.\n'
        'Rules:\n'
        '- Modern neutral American English, suitable for adult learners.\n'
        '- 4–14 words in English; the headword must appear exactly as given.\n'
        '- No templates like "I like X" or "This is X".\n'
        '- Russian must match the English meaning precisely.\n'
        'Return JSON: {"items": [{"word": "...", "example": "...", "example_ru": "..."}]}\n'
        f'Words: {json.dumps(items, ensure_ascii=False)}'
    )
    provider = get_provider()
    if provider.name == 'mock':
        return {}

    result = await provider.chat(
        [ChatMessage(role='user', content=prompt)],
        temperature=0.3,
        json_mode=True,
        max_tokens=2500,
    )
    data = json.loads(result.text)
    out: dict[str, dict[str, str]] = {}
    for item in data.get('items') or []:
        if not isinstance(item, dict):
            continue
        word = str(item.get('word', '')).strip().lower()
        ex = str(item.get('example', '')).strip()
        ex_ru = str(item.get('example_ru', '')).strip()
        if word and ex and ex_ru:
            out[word] = {'example': ex, 'example_ru': ex_ru}
    return out


class Command(BaseCommand):
    help = 'Fill missing example sentences for a CEFR level into {level}_examples.json'

    def add_arguments(self, parser):
        parser.add_argument('--level', required=True, choices=CEFR_LEVELS)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=0, help='Max words to generate')
        parser.add_argument('--data-dir', default='')

    def handle(self, *args, **options):
        level = options['level'].lower()
        data_dir = Path(options['data_dir'] or settings.BASE_DIR / 'learning' / 'data' / 'word_bank')
        lookup = load_level_examples(level, data_dir=data_dir)

        missing: list[dict] = []
        for entry in WordBankEntry.objects.filter(
            is_active=True,
            cefr_level=level,
        ).order_by('english'):
            row = {
                'english': entry.english,
                'translation': entry.translation,
                'cefr_level': level,
                'part_of_speech': entry.part_of_speech,
                'example': entry.example,
                'example_ru': entry.example_ru,
            }
            if is_valid_context_example(enrich_row_examples(dict(row), tatoeba_lookup=lookup)):
                continue
            cached = lookup.get(entry.english.lower())
            if cached and is_valid_context_example(
                row,
                example=cached['example'],
                example_ru=cached['example_ru'],
            ):
                continue
            missing.append(row)

        active = WordBankEntry.objects.filter(is_active=True, cefr_level=level).count()
        with_ex = sum(
            1
            for entry in WordBankEntry.objects.filter(is_active=True, cefr_level=level)
            if is_valid_context_example({
                'english': entry.english,
                'translation': entry.translation,
                'cefr_level': level,
                'example': entry.example,
                'example_ru': entry.example_ru,
            })
        )
        self.stdout.write(f'{level.upper()} active: {active}, with examples in DB: {with_ex}')
        self.stdout.write(f'Missing examples: {len(missing)}')

        if options['dry_run'] or not missing:
            return

        limit = options['limit'] or len(missing)
        to_fill = missing[:limit]
        generated = 0

        for start in range(0, len(to_fill), BATCH_SIZE):
            batch = to_fill[start:start + BATCH_SIZE]
            try:
                batch_out = asyncio.run(_generate_batch(batch, level=level))
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f'Batch failed: {exc}')
                continue
            for row in batch:
                key = row['english'].lower()
                candidate = batch_out.get(key)
                if not candidate:
                    continue
                if not is_valid_context_example(
                    row,
                    example=candidate['example'],
                    example_ru=candidate['example_ru'],
                ):
                    continue
                lookup[key] = candidate
                generated += 1

        path = save_level_examples(level, lookup, data_dir=data_dir)
        self.stdout.write(self.style.SUCCESS(f'Generated {generated} examples → {path}'))
        self.stdout.write(
            f'Re-run: python manage.py seed_word_bank --include-remote --apply-quotas --level {level}',
        )
