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

BATCH_SIZE = 12
MAX_UNTIL_COMPLETE_ROUNDS = 8

_LEVEL_PROMPT = {
    'a1': 'A1 beginner — very simple daily situations',
    'a2': 'A2 elementary — everyday routines, travel, shopping',
    'b1': 'B1 intermediate — work, news, opinions, real conversations',
    'b2': 'B2 upper-intermediate — abstract topics, nuance, professional life',
    'c1': 'C1 advanced — precise, natural, educated speech',
}

_SYSTEM = (
    'You write example sentences for an American English tutor app used by Russian adults. '
    'Every sentence must sound like something a real person would say in the United States today — '
    'not textbook filler, not British English, not nonsense.'
)


def _build_prompt(batch: list[dict], *, level: str) -> str:
    level_label = _LEVEL_PROMPT.get(level, level.upper())
    items = [
        {
            'word': row['english'],
            'translation_ru': row['translation'],
            'part_of_speech': row.get('part_of_speech') or '',
        }
        for row in batch
    ]
    return (
        f'Write ONE example sentence per headword ({level_label}).\n\n'
        'Requirements:\n'
        '- American English only (US spelling: color, center, organize).\n'
        '- Natural spoken register — what people actually say at work, home, or on the street.\n'
        '- Use the headword in its correct sense (match translation_ru).\n'
        '- 4–14 words; headword must appear exactly as given.\n'
        '- Concrete situation — not abstract definitions.\n'
        '- Accurate Russian translation of the full sentence.\n\n'
        'Never use:\n'
        '- "I like …", "This is …", "I want …" as the whole sentence pattern\n'
        '- British spellings (colour, favourite, centre)\n'
        '- Made-up or absurd contexts\n\n'
        'Return JSON: {"items": [{"word": "...", "example": "...", "example_ru": "..."}]}\n'
        f'Words: {json.dumps(items, ensure_ascii=False)}'
    )


async def _generate_batch(
    batch: list[dict],
    *,
    level: str,
    temperature: float = 0.2,
) -> dict[str, dict[str, str]]:
    from ai_app.services.registry import get_provider
    from ai_app.services.types import ChatMessage

    provider = get_provider()
    if provider.name == 'mock':
        return {}

    result = await provider.chat(
        [
            ChatMessage(role='system', content=_SYSTEM),
            ChatMessage(role='user', content=_build_prompt(batch, level=level)),
        ],
        temperature=temperature,
        json_mode=True,
        max_tokens=2800,
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


def _collect_missing(
    level: str,
    lookup: dict[str, dict[str, str]],
) -> list[dict]:
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
        cached = lookup.get(entry.english.lower())
        if cached and is_valid_context_example(
            row,
            example=cached['example'],
            example_ru=cached['example_ru'],
        ):
            continue
        if is_valid_context_example(enrich_row_examples(dict(row), tatoeba_lookup=lookup)):
            continue
        missing.append(row)
    return missing


def _apply_batch_results(
    batch: list[dict],
    batch_out: dict[str, dict[str, str]],
    lookup: dict[str, dict[str, str]],
) -> tuple[int, int]:
    generated = 0
    rejected = 0
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
            rejected += 1
            continue
        lookup[key] = candidate
        generated += 1
    return generated, rejected


def _fill_missing(
    missing: list[dict],
    *,
    level: str,
    lookup: dict[str, dict[str, str]],
    limit: int,
) -> tuple[int, int]:
    to_fill = missing[:limit]
    generated = 0
    rejected = 0

    for start in range(0, len(to_fill), BATCH_SIZE):
        batch = to_fill[start:start + BATCH_SIZE]
        try:
            batch_out = asyncio.run(_generate_batch(batch, level=level))
        except Exception:
            batch_out = {}
        g, r = _apply_batch_results(batch, batch_out, lookup)
        generated += g
        rejected += r

    still_missing = [
        row for row in to_fill
        if row['english'].lower() not in lookup
        or not is_valid_context_example(
            row,
            example=lookup[row['english'].lower()]['example'],
            example_ru=lookup[row['english'].lower()]['example_ru'],
        )
    ]
    for row in still_missing:
        try:
            batch_out = asyncio.run(
                _generate_batch([row], level=level, temperature=0.35),
            )
        except Exception:
            continue
        g, r = _apply_batch_results([row], batch_out, lookup)
        generated += g
        rejected += r

    return generated, rejected


class Command(BaseCommand):
    help = 'Fill missing example sentences for a CEFR level into {level}_examples.json'

    def add_arguments(self, parser):
        parser.add_argument('--level', required=True, choices=CEFR_LEVELS)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=0, help='Max words to generate')
        parser.add_argument('--until-complete', action='store_true',
                            help='Repeat until no gaps or max rounds reached')
        parser.add_argument('--data-dir', default='')

    def handle(self, *args, **options):
        level = options['level'].lower()
        data_dir = Path(options['data_dir'] or settings.BASE_DIR / 'learning' / 'data' / 'word_bank')
        lookup = load_level_examples(level, data_dir=data_dir)
        missing = _collect_missing(level, lookup)

        active = WordBankEntry.objects.filter(is_active=True, cefr_level=level).count()
        self.stdout.write(f'{level.upper()} active: {active}')
        self.stdout.write(f'Missing examples: {len(missing)}')

        if options['dry_run'] or not missing:
            return

        until_complete = options['until_complete']
        max_rounds = MAX_UNTIL_COMPLETE_ROUNDS if until_complete else 1
        total_generated = 0
        total_rejected = 0

        for round_num in range(1, max_rounds + 1):
            if not missing:
                break
            if until_complete and max_rounds > 1:
                self.stdout.write(f'Round {round_num}/{max_rounds}: {len(missing)} missing')

            limit = options['limit'] or len(missing)
            generated, rejected = _fill_missing(
                missing, level=level, lookup=lookup, limit=limit,
            )
            total_generated += generated
            total_rejected += rejected
            save_level_examples(level, lookup, data_dir=data_dir)
            missing = _collect_missing(level, lookup)
            if not generated and missing:
                break

        path = save_level_examples(level, lookup, data_dir=data_dir)
        self.stdout.write(self.style.SUCCESS(
            f'Generated {total_generated} examples ({total_rejected} rejected) → {path}',
        ))
        self.stdout.write(f'Still missing: {len(missing)}')
        if missing:
            sample = ', '.join(row['english'] for row in missing[:12])
            self.stderr.write(f'Gap words: {sample}')
        self.stdout.write(
            f'Re-run: python manage.py seed_word_bank --include-remote --apply-quotas --level {level}',
        )
