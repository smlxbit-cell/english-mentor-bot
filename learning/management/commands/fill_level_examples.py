"""Generate missing usage examples for a CEFR level via AI (American EN + RU)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from learning.models import WordBankEntry
from learning.word_bank.example_enrich import enrich_row_examples, is_valid_context_example
from learning.word_bank.level_examples import (
    EXAMPLES_PER_WORD,
    examples_path,
    load_level_examples,
    save_level_examples,
)

MIN_EXAMPLES = 2
from learning.word_bank.level_quotas import CEFR_LEVELS

BATCH_SIZE = 8
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
        f'Write THREE different example sentences per headword ({level_label}).\n\n'
        'Requirements:\n'
        '- American English only (US spelling: color, center, organize).\n'
        '- Natural spoken register — what people actually say at work, home, or on the street.\n'
        '- Use the headword in its correct sense (match translation_ru).\n'
        '- 4–14 words each; headword must appear exactly as given.\n'
        '- Three distinct situations — not paraphrases of the same line.\n'
        '- Accurate Russian translation of each full sentence.\n\n'
        'Never use:\n'
        '- "I like …", "This is …", "I want …" as the whole sentence pattern\n'
        '- British spellings (colour, favourite, centre)\n'
        '- Made-up or absurd contexts\n\n'
        'Return JSON: {"items": [{"word": "...", "examples": ['
        '{"example": "...", "example_ru": "..."}, ...]}]}\n'
        f'Words: {json.dumps(items, ensure_ascii=False)}'
    )


async def _generate_batch(
    batch: list[dict],
    *,
    level: str,
    temperature: float = 0.2,
) -> dict[str, list[dict[str, str]]]:
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
        max_tokens=4000,
    )
    data = json.loads(result.text)
    out: dict[str, list[dict[str, str]]] = {}
    for item in data.get('items') or []:
        if not isinstance(item, dict):
            continue
        word = str(item.get('word', '')).strip().lower()
        examples: list[dict[str, str]] = []
        for ex_item in item.get('examples') or []:
            if not isinstance(ex_item, dict):
                continue
            ex = str(ex_item.get('example', '')).strip()
            ex_ru = str(ex_item.get('example_ru', '')).strip()
            if ex and ex_ru:
                examples.append({'example': ex, 'example_ru': ex_ru})
        if word and examples:
            out[word] = examples
    return out


def _valid_example_count(row: dict, lookup: dict[str, dict]) -> int:
    cached = lookup.get(row['english'].lower()) or {}
    examples = cached.get('examples') or []
    if not examples and cached.get('example'):
        examples = [{'example': cached['example'], 'example_ru': cached['example_ru']}]
    count = 0
    for ex in examples:
        if is_valid_context_example(
            row,
            example=ex.get('example', ''),
            example_ru=ex.get('example_ru', ''),
        ):
            count += 1
    enriched = enrich_row_examples(dict(row), tatoeba_lookup=lookup)
    if is_valid_context_example(enriched):
        count = max(count, 1)
    return count


def _collect_missing(
    level: str,
    lookup: dict[str, dict],
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
        if _valid_example_count(row, lookup) >= MIN_EXAMPLES:
            continue
        missing.append(row)
    return missing


def _apply_batch_results(
    batch: list[dict],
    batch_out: dict[str, list[dict[str, str]]],
    lookup: dict[str, dict],
) -> tuple[int, int]:
    generated = 0
    rejected = 0
    for row in batch:
        key = row['english'].lower()
        candidates = batch_out.get(key) or []
        valid: list[dict[str, str]] = []
        for candidate in candidates:
            if is_valid_context_example(
                row,
                example=candidate['example'],
                example_ru=candidate['example_ru'],
            ):
                valid.append(candidate)
        if len(valid) < MIN_EXAMPLES:
            rejected += 1
            continue
        lookup[key] = {
            'examples': valid[:EXAMPLES_PER_WORD],
            'example': valid[0]['example'],
            'example_ru': valid[0]['example_ru'],
        }
        generated += 1
    return generated, rejected


def _fill_missing(
    missing: list[dict],
    *,
    level: str,
    lookup: dict[str, dict],
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
        if _valid_example_count(row, lookup) < MIN_EXAMPLES
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
        parser.add_argument(
            '--until-complete',
            action='store_true',
            help='Repeat until no gaps or max rounds reached',
        )
        parser.add_argument('--data-dir', default='')

    def handle(self, *args, **options):
        level = options['level'].lower()
        data_dir = Path(options['data_dir'] or settings.BASE_DIR / 'learning' / 'data' / 'word_bank')
        lookup = load_level_examples(level, data_dir=data_dir)
        missing = _collect_missing(level, lookup)

        active = WordBankEntry.objects.filter(is_active=True, cefr_level=level).count()
        self.stdout.write(f'{level.upper()} active: {active}')
        self.stdout.write(
            f'Missing examples (<{MIN_EXAMPLES} each): {len(missing)}',
        )

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

        save_level_examples(level, lookup, data_dir=data_dir)
        self.stdout.write(self.style.SUCCESS(
            f'Generated {total_generated} word sets ({total_rejected} rejected) → '
            f'{examples_path(level, data_dir=data_dir)}',
        ))
        self.stdout.write(f'Still missing: {len(missing)}')
        if missing:
            sample = ', '.join(row['english'] for row in missing[:12])
            self.stderr.write(f'Gap words: {sample}')
        self.stdout.write(
            f'Re-run: python manage.py seed_word_bank --include-remote --apply-quotas --level {level}',
        )
