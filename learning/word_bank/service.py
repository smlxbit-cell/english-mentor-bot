"""Word bank stats, user marking, and daily learning picks."""

from __future__ import annotations

import random
from typing import Any

from django.db.models import Count, Q
from django.utils import timezone

from learning.models import Word, WordBankEntry
from learning.word_bank.normalize import word_slug
from progress_app.models import UserWordBankStatus, UserWordProgress

CEFR_LEVELS = ('a1', 'a2', 'b1', 'b2', 'c1')
LEVEL_INDEX = {level: idx for idx, level in enumerate(CEFR_LEVELS)}

# Approximate CEFR vocabulary targets (for display when bank is still growing).
RECOMMENDED_TARGETS = {
    'a1': 500,
    'a2': 1000,
    'b1': 2000,
    'b2': 3500,
    'c1': 5000,
}

DAILY_NEW_WORDS = 10
SURVEY_BATCH = 10


def _levels_up_to(level: str) -> list[str]:
    level = (level or 'a1').lower()
    if level not in LEVEL_INDEX:
        level = 'a1'
    idx = LEVEL_INDEX[level]
    return list(CEFR_LEVELS[: idx + 1])


def _progress_bar(known: int, total: int, width: int = 10) -> str:
    if total <= 0:
        return '░' * width
    filled = max(0, min(width, round(width * known / total)))
    return '█' * filled + '░' * (width - filled)


def sync_word_from_bank(user_id: int, entry: WordBankEntry, *, status: str) -> Word:
    word, _ = Word.objects.get_or_create(
        english=entry.english,
        defaults={
            'translation': entry.translation,
            'example': entry.example,
        },
    )
    changed = False
    if not word.translation and entry.translation:
        word.translation = entry.translation
        changed = True
    if not word.example and entry.example:
        word.example = entry.example
        changed = True
    if changed:
        word.save(update_fields=['translation', 'example', 'updated_at'])

    defaults: dict[str, Any] = {}
    if status == UserWordBankStatus.Status.KNOWN:
        defaults = {
            'status': UserWordProgress.Status.KNOWN,
            'strength': 1.0,
            'next_review_at': None,
        }
    elif status == UserWordBankStatus.Status.LEARNING:
        defaults = {
            'status': UserWordProgress.Status.NEW,
            'next_review_at': timezone.now(),
        }

    UserWordProgress.objects.update_or_create(
        user_id=user_id,
        word=word,
        defaults=defaults,
    )
    return word


def mark_bank_entry(user_id: int, bank_entry_id: int, status: str) -> WordBankEntry | None:
    entry = WordBankEntry.objects.filter(id=bank_entry_id, is_active=True).first()
    if not entry:
        return None
    UserWordBankStatus.objects.update_or_create(
        user_id=user_id,
        bank_entry=entry,
        defaults={'status': status},
    )
    if status in (
        UserWordBankStatus.Status.KNOWN,
        UserWordBankStatus.Status.LEARNING,
    ):
        sync_word_from_bank(user_id, entry, status=status)
    return entry


def _status_counts(user_id: int, level: str) -> dict[str, int]:
    qs = UserWordBankStatus.objects.filter(
        user_id=user_id,
        bank_entry__cefr_level=level,
        bank_entry__is_active=True,
    )
    agg = qs.values('status').annotate(c=Count('id'))
    counts = {row['status']: row['c'] for row in agg}
    return {
        'known': counts.get(UserWordBankStatus.Status.KNOWN, 0),
        'learning': counts.get(UserWordBankStatus.Status.LEARNING, 0),
        'skipped': counts.get(UserWordBankStatus.Status.SKIPPED, 0),
    }


def get_level_stats(user_id: int, level: str) -> dict[str, Any]:
    level = level.lower()
    bank_total = WordBankEntry.objects.filter(cefr_level=level, is_active=True).count()
    counts = _status_counts(user_id, level)
    known = counts['known']
    learning = counts['learning']
    marked = known + learning + counts['skipped']
    unseen = max(0, bank_total - marked)
    target = max(bank_total, RECOMMENDED_TARGETS.get(level, bank_total))
    return {
        'level': level,
        'bank_total': bank_total,
        'target': target,
        'known': known,
        'learning': learning,
        'unseen': unseen,
        'remaining': max(0, target - known),
        'bar': _progress_bar(known, target),
        'pct': round(100 * known / target, 1) if target else 0,
    }


def get_word_bank_overview(user_id: int, user_level: str) -> dict[str, Any]:
    levels = _levels_up_to(user_level)
    level_stats = [get_level_stats(user_id, lvl) for lvl in levels]
    due_count = UserWordProgress.objects.filter(
        user_id=user_id,
        status__in=(
            UserWordProgress.Status.NEW,
            UserWordProgress.Status.LEARNING,
        ),
    ).filter(
        Q(next_review_at__lte=timezone.now()) | Q(next_review_at__isnull=True),
    ).count()
    unseen_total = sum(s['unseen'] for s in level_stats)
    return {
        'user_level': (user_level or 'a1').lower(),
        'levels': level_stats,
        'due_count': due_count,
        'unseen_total': unseen_total,
        'daily_new': DAILY_NEW_WORDS,
    }


def pick_unseen_entries(
    user_id: int,
    user_level: str,
    *,
    limit: int = SURVEY_BATCH,
) -> list[WordBankEntry]:
    levels = _levels_up_to(user_level)
    marked_ids = UserWordBankStatus.objects.filter(user_id=user_id).values_list(
        'bank_entry_id', flat=True,
    )
    qs = (
        WordBankEntry.objects.filter(is_active=True, cefr_level__in=levels)
        .exclude(id__in=marked_ids)
        .order_by('cefr_level', 'english')
    )
    # Prefer lower levels first, shuffle within each level band.
    by_level: dict[str, list[WordBankEntry]] = {lvl: [] for lvl in levels}
    for entry in qs[: limit * 8]:
        by_level.setdefault(entry.cefr_level, []).append(entry)
    picked: list[WordBankEntry] = []
    for lvl in levels:
        pool = by_level.get(lvl) or []
        random.shuffle(pool)
        for entry in pool:
            picked.append(entry)
            if len(picked) >= limit:
                return picked
    return picked


def pick_daily_learning_entries(
    user_id: int,
    user_level: str,
    *,
    limit: int = DAILY_NEW_WORDS,
) -> list[WordBankEntry]:
    """Unseen words for today's learning session (auto-marked as learning)."""
    entries = pick_unseen_entries(user_id, user_level, limit=limit)
    for entry in entries:
        mark_bank_entry(user_id, entry.id, UserWordBankStatus.Status.LEARNING)
    return entries


def format_word_hub_text(overview: dict[str, Any]) -> str:
    lines = [
        '📚 <b>Слова</b>',
        '',
        'Прогресс по уровням (знаю / цель):',
    ]
    for stat in overview['levels']:
        lvl = stat['level'].upper()
        lines.append(
            f"{lvl} {stat['bar']} "
            f"<b>{stat['known']}</b>/{stat['target']} · учу {stat['learning']}"
        )
    lines.extend([
        '',
        f"🆕 Не размечено: <b>{overview['unseen_total']}</b> · "
        f"🔄 К повторению: <b>{overview['due_count']}</b>",
        '',
        f"План на сегодня: <b>{overview['daily_new']}</b> новых слов + повторение.",
    ])
    return '\n'.join(lines)


def entry_to_dict(entry: WordBankEntry) -> dict[str, Any]:
    return {
        'bank_entry_id': entry.id,
        'english': entry.english,
        'translation': entry.translation,
        'example': entry.example,
        'example_ru': entry.example_ru,
        'cefr_level': entry.cefr_level,
    }


def get_review_words_for_entries(profile_id: int, entries: list[WordBankEntry]) -> list[dict]:
    """Build SRS review queue from bank entries (Word rows must exist)."""
    words = Word.objects.filter(english__in=[e.english for e in entries])
    word_by_en = {w.english.lower(): w for w in words}
    out = []
    for entry in entries:
        word = word_by_en.get(entry.english.lower())
        if not word:
            word = sync_word_from_bank(
                profile_id, entry, status=UserWordBankStatus.Status.LEARNING,
            )
        out.append({
            'word_id': word.id,
            'english': word.english,
            'translation': word.translation or entry.translation,
            'example': word.example or entry.example,
            'bank_entry_id': entry.id,
        })
    return out
