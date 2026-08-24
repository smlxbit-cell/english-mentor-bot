"""Generate missing A1 usage examples via AI (American English + accurate RU)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from learning.models import WordBankEntry
from learning.word_bank.example_enrich import enrich_row_examples, is_valid_context_example

A1_EXAMPLES_FILE = 'a1_examples.json'
BATCH_SIZE = 15


def _examples_path(data_dir: Path) -> Path:
    return data_dir / A1_EXAMPLES_FILE


def load_a1_examples(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return {}
    return {
        str(k).lower(): {
            'example': str(v.get('example', '')).strip(),
            'example_ru': str(v.get('example_ru', '')).strip(),
        }
        for k, v in data.items()
        if isinstance(v, dict)
    }


def save_a1_examples(path: Path, lookup: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lookup, ensure_ascii=False, indent=2), encoding='utf-8')


async def _generate_batch(batch: list[dict]) -> dict[str, dict[str, str]]:
    from ai_app.services.registry import get_provider
    from ai_app.services.types import ChatMessage

    items = [
        {
            'word': row['english'],
            'translation': row['translation'],
            'pos': row.get('part_of_speech') or '',
        }
        for row in batch
    ]
    prompt = (
        'For each English headword, write ONE natural American English sentence (A1 level) '
        'that uses the word correctly, plus an accurate Russian translation.\n'
        'Rules:\n'
        '- Modern neutral American English, suitable for adult learners.\n'
        '- 4–12 words in English; the headword must appear exactly as given.\n'
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
        max_tokens=2000,
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
    help = 'Fill missing A1 example sentences (AI + validation) into a1_examples.json'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=0, help='Max words to generate')
        parser.add_argument('--data-dir', default='')

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'] or settings.BASE_DIR / 'learning' / 'data' / 'word_bank')
        path = _examples_path(data_dir)
        lookup = load_a1_examples(path)

        missing: list[dict] = []
        for entry in WordBankEntry.objects.filter(is_active=True, cefr_level='a1').order_by('english'):
            row = {
                'english': entry.english,
                'translation': entry.translation,
                'cefr_level': 'a1',
                'part_of_speech': entry.part_of_speech,
                'example': entry.example,
                'example_ru': entry.example_ru,
            }
            enriched = enrich_row_examples(row, tatoeba_lookup=lookup)
            if is_valid_context_example(enriched):
                continue
            if entry.english.lower() in lookup and is_valid_context_example(
                row,
                example=lookup[entry.english.lower()]['example'],
                example_ru=lookup[entry.english.lower()]['example_ru'],
            ):
                continue
            missing.append(row)

        self.stdout.write(f'A1 active: {WordBankEntry.objects.filter(is_active=True, cefr_level="a1").count()}')
        self.stdout.write(f'Missing examples: {len(missing)}')

        if options['dry_run'] or not missing:
            return

        limit = options['limit'] or len(missing)
        to_fill = missing[:limit]
        generated = 0

        for start in range(0, len(to_fill), BATCH_SIZE):
            batch = to_fill[start:start + BATCH_SIZE]
            try:
                batch_out = asyncio.run(_generate_batch(batch))
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

        save_a1_examples(path, lookup)
        self.stdout.write(self.style.SUCCESS(f'Generated {generated} examples → {path}'))

        if not options['dry_run'] and generated:
            self.stdout.write('Re-run: python manage.py seed_word_bank --include-remote --apply-quotas --level a1')
