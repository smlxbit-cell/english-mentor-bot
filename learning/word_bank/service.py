"""Word bank stats, user marking, and daily learning picks."""

from __future__ import annotations

import random
from typing import Any

from django.db.models import Count, Q
from django.utils import timezone

from learning.models import Word, WordBankEntry
from learning.word_bank.navigation import PAGE_SIZE, canonical_topic, normalize_topics, topic_label
from learning.word_bank.topic_classifier import topic_matches
from progress_app.models import UserWordBankStatus, UserWordProgress

CEFR_LEVELS = ('a1', 'a2', 'b1', 'b2', 'c1')
LEVEL_INDEX = {level: idx for idx, level in enumerate(CEFR_LEVELS)}

# CEFR vocabulary goals for progress display (known / target per band).
# Each level has its own word set — not cumulative totals.
from learning.word_bank.level_quotas import LEVEL_TARGETS as RECOMMENDED_TARGETS

DAILY_NEW_WORDS = 10
MIN_LEARNING_QUEUE = 10
SURVEY_BATCH = 10
SURVEY_LEVEL_MAX = 80


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


def words_count_ru(n: int) -> str:
    """«1 слово», «43 слова», «5 слов»."""
    n_abs = abs(int(n))
    mod10, mod100 = n_abs % 10, n_abs % 100
    if mod10 == 1 and mod100 != 11:
        form = 'слово'
    elif 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
        form = 'слова'
    else:
        form = 'слов'
    return f'{n} {form}'


def format_word_stats_line(summary: dict[str, Any]) -> str:
    """Единый формат: всего · учить · уже знаю (known + mastered)."""
    already = summary.get('known', 0) + summary.get('mastered', 0)
    return (
        f'Всего <b>{summary["total"]}</b> · '
        f'учить <b>{summary["learning"]}</b> · '
        f'уже знаю <b>{already}</b>'
    )


def format_training_queue_line(summary: dict[str, Any]) -> str:
    """Compact «учить N» for list pages."""
    learning = summary.get('learning', 0)
    if learning <= 0:
        return ''
    return f'📗 учить <b>{learning}</b>'


def _learning_bank_english(user_id: int) -> list[str]:
    """Headwords explicitly marked «учить» in the bank."""
    return [
        en for en in UserWordBankStatus.objects.filter(
            user_id=user_id,
            status=UserWordBankStatus.Status.LEARNING,
        ).values_list('bank_entry__english', flat=True)
        if en
    ]


def _known_bank_english(user_id: int) -> list[str]:
    return [
        en for en in UserWordBankStatus.objects.filter(
            user_id=user_id,
            status=UserWordBankStatus.Status.KNOWN,
        ).values_list('bank_entry__english', flat=True)
        if en
    ]


def count_learning_due(user_id: int) -> int:
    """Words marked «учить» that are ready for SRS now (same rules as get_due_words)."""
    learning = _learning_bank_english(user_id)
    if not learning:
        return 0
    now = timezone.now()
    due: set[str] = set()
    progressed: set[str] = set()
    qs = UserWordProgress.objects.filter(
        user_id=user_id,
        word__english__in=learning,
    )
    for en, next_at, st in qs.values_list(
        'word__english', 'next_review_at', 'status',
    ):
        progressed.add(en.lower())
        if st == UserWordProgress.Status.KNOWN and next_at is None:
            continue
        if next_at is None or next_at <= now:
            due.add(en.lower())
    for en in learning:
        if en.lower() not in progressed:
            due.add(en.lower())
    return len(due)


def sync_word_from_bank(user_id: int, entry: WordBankEntry, *, status: str) -> Word:
    word, _ = Word.objects.get_or_create(
        english=entry.english,
        defaults={
            'translation': entry.translation,
            'example': entry.example,
        },
    )
    changed = False
    if entry.translation and word.translation != entry.translation:
        word.translation = entry.translation
        changed = True
    if entry.example and word.example != entry.example:
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


def refresh_words_from_bank() -> int:
    """Push canonical WordBankEntry text into learner Word rows."""
    updated = 0
    for entry in WordBankEntry.objects.filter(is_active=True).only(
        'english', 'translation', 'example',
    ):
        rows = Word.objects.filter(english__iexact=entry.english)
        for word in rows:
            fields: list[str] = []
            if entry.translation and word.translation != entry.translation:
                word.translation = entry.translation
                fields.append('translation')
            if entry.example and word.example != entry.example:
                word.example = entry.example
                fields.append('example')
            if fields:
                fields.append('updated_at')
                word.save(update_fields=fields)
                updated += 1
    return updated


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
    target = RECOMMENDED_TARGETS.get(level, bank_total or 1)
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
    level_stats = [get_level_stats(user_id, lvl) for lvl in CEFR_LEVELS]
    stats_by_level = {s['level']: s for s in level_stats}
    path_levels = _levels_up_to(user_level)
    unseen_total = sum(stats_by_level[l]['unseen'] for l in path_levels if l in stats_by_level)
    due_count = count_learning_due(user_id)
    user_lvl = (user_level or 'a1').lower()
    current_level = stats_by_level.get(user_lvl) or (level_stats[-1] if level_stats else None)
    return {
        'user_level': user_lvl,
        'levels': level_stats,
        'current_level': current_level,
        'due_count': due_count,
        'unseen_total': unseen_total,
        'unseen_at_level': current_level['unseen'] if current_level else 0,
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


def pick_unseen_entries_for_level(
    user_id: int,
    level: str,
    *,
    limit: int = SURVEY_BATCH,
) -> list[WordBankEntry]:
    """Unseen words for one CEFR level (survey / check flow)."""
    level = (level or 'a1').lower()
    marked_ids = UserWordBankStatus.objects.filter(user_id=user_id).values_list(
        'bank_entry_id', flat=True,
    )
    qs = (
        WordBankEntry.objects.filter(is_active=True, cefr_level=level)
        .exclude(id__in=marked_ids)
        .order_by('english')
    )
    pool = list(qs[: limit * 4])
    random.shuffle(pool)
    return pool[:limit]


def pick_daily_intro_entries(
    user_id: int,
    user_level: str,
    *,
    limit: int = DAILY_NEW_WORDS,
) -> list[WordBankEntry]:
    """Unseen words at the user's CEFR level only (not lower levels)."""
    level = (user_level or 'a1').lower()
    return pick_unseen_entries_for_level(user_id, level, limit=limit)


def pick_practice_fallback_entries(
    user_id: int,
    user_level: str,
    interest_tokens: list[str] | None = None,
    *,
    limit: int = DAILY_NEW_WORDS,
) -> list[WordBankEntry]:
    """Unseen words at user level, shuffled; prefer the learner's interest topics."""
    from study_app.daily_facts import interest_tokens_to_topics

    level = (user_level or 'a1').lower()
    marked_ids = UserWordBankStatus.objects.filter(user_id=user_id).values_list(
        'bank_entry_id', flat=True,
    )
    pool = list(
        WordBankEntry.objects.filter(is_active=True, cefr_level=level)
        .exclude(id__in=marked_ids),
    )
    if not pool:
        return []

    preferred = interest_tokens_to_topics(interest_tokens or [])
    if preferred:
        matched = [
            entry for entry in pool
            if preferred.intersection(set(normalize_topics(entry.topics)))
        ]
        if len(matched) >= limit:
            pool = matched
        elif matched:
            rest = [entry for entry in pool if entry not in matched]
            random.shuffle(matched)
            random.shuffle(rest)
            pool = matched + rest

    random.shuffle(pool)
    return pool[:limit]


def prepare_practice_fallback_intro(
    user_id: int,
    user_level: str,
    interest_tokens: list[str] | None = None,
    *,
    limit: int = DAILY_NEW_WORDS,
) -> dict[str, Any]:
    entries = pick_practice_fallback_entries(
        user_id, user_level, interest_tokens, limit=limit,
    )
    return {'intro': [entry_to_dict(entry) for entry in entries]}


def ensure_min_learning_queue(
    user_id: int,
    user_level: str,
    interest_tokens: list[str] | None = None,
) -> int:
    """Top up «учить» to MIN_LEARNING_QUEUE only when below minimum."""
    learning = get_personal_dict_summary(user_id).get('learning', 0)
    if learning >= MIN_LEARNING_QUEUE:
        return 0
    need = MIN_LEARNING_QUEUE - learning
    entries = pick_practice_fallback_entries(
        user_id, user_level, interest_tokens, limit=need,
    )
    added = 0
    for entry in entries:
        mark_bank_entry(user_id, entry.id, UserWordBankStatus.Status.LEARNING)
        added += 1
    return added


def pick_training_words(
    user_id: int,
    user_level: str,
    *,
    limit: int = DAILY_NEW_WORDS,
) -> list[dict]:
    """Batch for practice: due first, then any «учить» words."""
    from progress_app.models import UserWordProgress

    del user_level
    learning_en = _learning_bank_english(user_id)
    if not learning_en:
        return []

    now = timezone.now()
    out: list[dict] = []
    seen: set[str] = set()

    def _append_from_english(en: str, word_id: int | None) -> None:
        if len(out) >= limit or en.lower() in seen:
            return
        entry = WordBankEntry.objects.filter(
            english__iexact=en, is_active=True,
        ).first()
        if not entry:
            return
        row = entry_to_dict(entry)
        row['word_id'] = word_id
        out.append(row)
        seen.add(en.lower())

    due_qs = (
        UserWordProgress.objects.filter(
            user_id=user_id,
            word__english__in=learning_en,
        )
        .filter(Q(next_review_at__lte=now) | Q(next_review_at__isnull=True))
        .exclude(status=UserWordProgress.Status.KNOWN, next_review_at__isnull=True)
        .select_related('word')
        .order_by('next_review_at')
    )
    for uwp in due_qs:
        if len(out) >= limit:
            break
        _append_from_english(uwp.word.english, uwp.word_id)

    if len(out) < limit:
        for en in learning_en:
            if len(out) >= limit:
                break
            _append_from_english(en, None)

    return out


def get_review_words_for_dicts(
    profile_id: int,
    word_dicts: list[dict],
) -> list[dict]:
    """Build drill queue from survey/page word dicts (already marked in bank)."""
    ids = [w['bank_entry_id'] for w in word_dicts if w.get('bank_entry_id')]
    if not ids:
        return []
    entries = list(WordBankEntry.objects.filter(id__in=ids, is_active=True))
    return get_review_words_for_entries(profile_id, entries)


def commit_daily_learning_entries(
    user_id: int,
    entries: list[WordBankEntry],
) -> None:
    """Mark picked words as «учу» when user starts the training quiz."""
    for entry in entries:
        mark_bank_entry(user_id, entry.id, UserWordBankStatus.Status.LEARNING)


def format_word_hub_text(overview: dict[str, Any]) -> str:
    user_lvl = overview['user_level'].upper()
    learning_total = sum(s['learning'] for s in overview['levels'])
    lines = [
        '📚 <b>Слова</b>',
        '',
        f'Твой уровень: <b>{user_lvl}</b> · по результатам теста',
        '',
    ]
    for stat in overview['levels']:
        lvl = stat['level'].upper()
        here = ' ← ты здесь' if stat['level'] == overview['user_level'] else ''
        lines.append(
            f"{lvl} {stat['bar']} "
            f"<b>{stat['known']}</b>/{stat['target']} · учить {stat['learning']}{here}"
        )
    lines.extend([
        '',
        f'🎯 <b>Тренировка</b> — {words_count_ru(learning_total)}',
    ])
    return '\n'.join(lines)


def format_word_new_section_text(overview: dict[str, Any]) -> str:
    n = overview['daily_new']
    lvl = overview['user_level'].upper()
    return (
        f'📘 <b>Словарь · {lvl}</b>\n\n'
        f'«Начать · {n}» — {n} слов вашего уровня\n'
        '«Из словаря» — добавить вручную'
    )


def format_word_new_pick_text(overview: dict[str, Any]) -> str:
    lvl = overview['user_level'].upper()
    return (
        f'📘 <b>Словарь · {lvl}</b>\n\n'
        'Отметьте слова «🎯 Учить» или «✅ Знаю» — потом тренировка из «учить».'
    )


def format_word_survey_levels_text(user_level: str) -> str:
    lvl = (user_level or 'a1').upper()
    return (
        '👀 <b>Что знаешь?</b>\n\n'
        f'Начните с <b>{lvl}</b> (★) — ваш уровень по тесту.\n'
        '10 слов подряд: только <b>знаю</b> или <b>учить</b>.\n'
        'В конце — сразу тренировка.'
    )


def _english_for_topic(topic: str, *, base_qs=None) -> list[str]:
    """Headwords matching a canonical topic (works with legacy DB tags)."""
    canon = canonical_topic(topic)
    qs = base_qs or WordBankEntry.objects.filter(is_active=True)
    rows = qs.only('english', 'topics')
    if canon == 'general':
        return [e.english for e in rows if normalize_topics(e.topics) == ['general']]
    return [e.english for e in rows if topic_matches(e.topics, canon)]


def format_word_repeat_section_text(
    overview: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    learning = summary.get('learning', 0)
    if learning == 0:
        return (
            '🎯 <b>Тренировка</b>\n\n'
            'Подберём <b>10 слов</b> вашего уровня по интересам — '
            'отметьте «🎯 Учить» или «✅ Знаю».'
        )
    stats = format_word_stats_line(summary)
    batch = min(learning, DAILY_NEW_WORDS)
    tail = f'\n\nЗа раз — <b>{batch}</b> из <b>{learning}</b>.'
    return f'🎯 <b>Тренировка</b>\n\n{stats}{tail}'


def format_word_review_intro(count: int) -> str:
    return (
        f'🎯 <b>Тренировка · {words_count_ru(count)}</b>\n\n'
        'Дам перевод — напишите или скажите слово по-английски.\n'
        '✍️ текст · 🎙️ голос'
    )


def format_word_review_prompt(*, pos: int, total: int, translation: str) -> str:
    return (
        f'<b>{pos}/{total}</b> · Как по-английски «{translation}»?\n'
        '✍️ Напишите · 🎙️ Скажите'
    )


def format_daily_intro_start(count: int) -> str:
    return (
        f'📘 <b>Урок · {words_count_ru(count)}</b>\n\n'
        'По одному слову:\n'
        '🔊 Слушайте → «Дальше» — в список «учить»\n'
        '«Знаю ✅» — уже знаете\n\n'
        'В конце — 🎯 тренировка.'
    )


def format_daily_intro_finish(count: int) -> str:
    return (
        f'✅ <b>{words_count_ru(count)} готово</b>\n\n'
        'Слова в списке «учить».\n'
        'Нажмите 🎯 <b>Тренировка</b> — перевод → ответ по-английски.'
    )


def entry_to_dict(entry: WordBankEntry) -> dict[str, Any]:
    from learning.english_display import display_word_fields
    from learning.word_bank.example_enrich import resolve_word_examples

    resolved = resolve_word_examples({
        'english': entry.english,
        'translation': entry.translation,
        'example': entry.example or '',
        'example_ru': entry.example_ru or '',
    })
    display = display_word_fields(
        english=entry.english,
        translation=entry.translation,
        example=resolved['example'],
        part_of_speech=entry.part_of_speech or '',
    )
    return {
        'bank_entry_id': entry.id,
        'english': display['english'],
        'translation': display['translation'],
        'example': display['example'],
        'example_ru': resolved['example_ru'],
        'cefr_level': entry.cefr_level,
        'topics': normalize_topics(entry.topics),
    }


def get_personal_dict_summary(user_id: int) -> dict[str, Any]:
    """Counts from explicit bank marks — not lesson vocabulary imports."""
    bank = UserWordBankStatus.objects.filter(user_id=user_id)
    learning = bank.filter(status=UserWordBankStatus.Status.LEARNING).count()
    known = bank.filter(status=UserWordBankStatus.Status.KNOWN).count()
    learning_en = _learning_bank_english(user_id)
    mastered = 0
    if learning_en:
        mastered = UserWordProgress.objects.filter(
            user_id=user_id,
            word__english__in=learning_en,
            status=UserWordProgress.Status.MASTERED,
        ).count()
    due = count_learning_due(user_id)
    return {
        'total': learning + known,
        'learning': learning,
        'known': known,
        'mastered': mastered,
        'due': due,
    }


def list_personal_words(
    user_id: int,
    *,
    status: str | None = None,
    level: str | None = None,
    topic: str | None = None,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> dict[str, Any]:
    learning_en = _learning_bank_english(user_id)
    known_en = _known_bank_english(user_id)
    qs = UserWordProgress.objects.filter(user_id=user_id).select_related('word')
    if status == 'learning':
        if not learning_en:
            qs = qs.none()
        else:
            qs = qs.filter(word__english__in=learning_en)
    elif status == 'known':
        english_set = known_en
        if english_set:
            qs = qs.filter(
                Q(word__english__in=english_set)
                | Q(status=UserWordProgress.Status.MASTERED),
            )
        else:
            qs = qs.filter(status=UserWordProgress.Status.MASTERED)
    elif status:
        qs = qs.filter(status=status)

    if level:
        english_set = WordBankEntry.objects.filter(
            cefr_level=level.lower(), is_active=True,
        ).values_list('english', flat=True)
        qs = qs.filter(word__english__in=english_set)
    if topic:
        english_set = _english_for_topic(topic)
        qs = qs.filter(word__english__in=english_set)

    qs = qs.order_by('-updated_at')
    total = qs.count()
    pages = max(1, (total + page_size - 1) // page_size)
    page = max(0, min(page, pages - 1))
    page_rows = list(qs[page * page_size:(page + 1) * page_size])
    english_on_page = [uwp.word.english for uwp in page_rows]
    bank_by_en = {
        e.english.lower(): e.id
        for e in WordBankEntry.objects.filter(
            english__in=english_on_page,
            is_active=True,
        ).only('id', 'english')
    }
    items = []
    for uwp in page_rows:
        items.append({
            'english': uwp.word.english,
            'translation': uwp.word.translation,
            'example': uwp.word.example,
            'status': uwp.status,
            'word_id': uwp.word_id,
            'bank_entry_id': bank_by_en.get(uwp.word.english.lower()),
        })
    return {'items': items, 'total': total, 'page': page, 'pages': pages}


def list_personal_topic_counts(user_id: int) -> list[tuple[str, int]]:
    qs = UserWordProgress.objects.filter(user_id=user_id).select_related('word')
    english_list = [uwp.word.english for uwp in qs]
    by_en = {
        e.english.lower(): e
        for e in WordBankEntry.objects.filter(english__in=english_list).only('english', 'topics')
    }
    counts: dict[str, int] = {}
    for uwp in qs:
        entry = by_en.get(uwp.word.english.lower())
        topics = normalize_topics(entry.topics if entry else None)
        for topic in topics:
            canon = canonical_topic(topic)
            counts[canon] = counts.get(canon, 0) + 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))


def list_bank_topic_counts(user_id: int, user_level: str) -> list[tuple[str, int]]:
    levels = _levels_up_to(user_level)
    marked = UserWordBankStatus.objects.filter(user_id=user_id).values_list(
        'bank_entry_id', flat=True,
    )
    entries = WordBankEntry.objects.filter(
        is_active=True, cefr_level__in=levels,
    ).exclude(id__in=marked).only('topics')
    counts: dict[str, int] = {}
    for entry in entries.iterator():
        for topic in normalize_topics(entry.topics):
            counts[topic] = counts.get(topic, 0) + 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))


def mark_bank_entries_bulk(
    user_id: int,
    bank_entry_ids: list[int],
    status: str,
) -> int:
    """Mark many bank entries; returns count successfully marked."""
    n = 0
    for eid in bank_entry_ids:
        if mark_bank_entry(user_id, eid, status) is not None:
            n += 1
    return n


def browse_bank_entries(
    user_id: int,
    user_level: str,
    *,
    level: str | None = None,
    topic: str | None = None,
    only_unseen: bool = True,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> dict[str, Any]:
    levels = [level.lower()] if level else _levels_up_to(user_level)
    qs = WordBankEntry.objects.filter(is_active=True, cefr_level__in=levels)
    if only_unseen:
        marked = UserWordBankStatus.objects.filter(user_id=user_id).values_list(
            'bank_entry_id', flat=True,
        )
        qs = qs.exclude(id__in=marked)
    if topic:
        canon = canonical_topic(topic)
        matched_ids = [
            e.id for e in qs.only('id', 'topics')
            if topic_matches(e.topics, canon)
        ]
        qs = qs.filter(id__in=matched_ids)
    qs = qs.order_by('cefr_level', 'english')
    total = qs.count()
    pages = max(1, (total + page_size - 1) // page_size)
    page = max(0, min(page, pages - 1))
    items = [entry_to_dict(e) for e in qs[page * page_size:(page + 1) * page_size]]
    return {
        'items': items,
        'total': total,
        'page': page,
        'pages': pages,
        'level': level,
        'topic': topic,
    }


def search_bank_entries(
    user_id: int,
    user_level: str,
    query: str,
    *,
    limit: int = 8,
) -> list[dict]:
    q = (query or '').strip()
    if len(q) < 2:
        return []
    levels = _levels_up_to(user_level)
    hits = WordBankEntry.objects.filter(
        is_active=True,
        cefr_level__in=levels,
    ).filter(
        Q(english__icontains=q) | Q(translation__icontains=q),
    ).order_by('cefr_level', 'english')[:limit]
    return [entry_to_dict(e) for e in hits]


def format_personal_dict_hub(summary: dict[str, Any]) -> str:
    if summary['total'] == 0:
        return (
            '📗 <b>Мои слова</b>\n\n'
            'Пока пусто. 📘 <b>Словарь</b> → «Начать · 10» '
            'или выбор вручную — отметьте «🎯 Учить».'
        )
    return (
        '📗 <b>Мои слова</b>\n\n'
        + format_word_stats_line(summary)
    )


def format_word_list_page(
    *,
    title: str,
    items: list[dict],
    page: int,
    pages: int,
    total: int,
    show_status: bool = False,
) -> str:
    lines = [f'<b>{title}</b>', '']
    if not items:
        lines.append('Здесь пока пусто.')
        return '\n'.join(lines)
    for w in items:
        if show_status:
            icon = {'new': '🆕', 'learning': '📗', 'known': '✅', 'mastered': '🌟'}.get(
                w.get('status'), '•',
            )
            lines.append(f'{icon} <b>{w["english"]}</b> — {w["translation"]}')
        else:
            lvl = (w.get('cefr_level') or '').upper()
            prefix = f'[{lvl}] ' if lvl else ''
            lines.append(f'{prefix}<b>{w["english"]}</b> — {w["translation"]}')
    lines.extend(['', f'Стр. {page + 1}/{pages} · всего {total}'])
    return '\n'.join(lines)


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
        row = entry_to_dict(entry)
        row['word_id'] = word.id
        out.append(row)
    return out
