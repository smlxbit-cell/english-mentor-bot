"""Build a personalized daily training plan (adventure chapter) per learner."""

from __future__ import annotations

import hashlib
from datetime import date

from django.db.models import Q
from django.utils import timezone

from content_app.models import Lesson
from study_app.daily_facts import DAILY_FACTS, GREETING_VARIANTS, warmup_label
from study_app.listening_bites import pick_listening_bite
from study_app.speaking_bites import pick_speaking_bite
from study_app.models import DailySession, DailySessionBlock, LessonProgress
from study_app.services.episode_routing import apply_story_placement, entry_level
from study_app.warmup_quiz import build_quiz_for_fact
from users_app.models import UserInterest, UserProfile

LEVEL_ORDER = ['a1', 'a2', 'b1', 'b2']

WARMUP_MINUTES = 3
RULE_DRILL_MINUTES = 5
SPEAKING_MINUTES = 4
LISTENING_MINUTES = 4
WEEKDAY_NAMES = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']


def _day_seed(user_id: int, day: date) -> int:
    raw = f'{user_id}:{day.isoformat()}'.encode()
    return int(hashlib.sha256(raw).hexdigest(), 16)


def effective_daily_minutes(profile: UserProfile) -> int:
    minutes = profile.daily_minutes or 20
    if minutes <= 10:
        return 20
    if minutes not in (20, 30, 60):
        return 20
    return minutes


def is_rest_day(profile: UserProfile, day: date) -> bool:
    rw = profile.rest_weekday
    if rw is None:
        rw = 6
    rw = int(rw)
    if rw > 6:  # 7 = no fixed rest day
        return False
    return day.weekday() == rw


def _pick_fact(user_id: int, day: date) -> dict:
    idx = _day_seed(user_id, day) % len(DAILY_FACTS)
    return DAILY_FACTS[idx]


def _pick_greeting(name: str, user_id: int, day: date, *, rest: bool = False) -> str:
    if rest:
        variants = [
            'Привет, {name}! Сегодня день отдыха — лёгкая разминка и всё 🌿',
            '{name}, сегодня в твоём плане день отдыха. Отдохни — прогресс не сгорит.',
        ]
        idx = (_day_seed(user_id, day) // 3) % len(variants)
        return variants[idx].format(name=name or 'друг')
    idx = (_day_seed(user_id, day) // 7) % len(GREETING_VARIANTS)
    return GREETING_VARIANTS[idx].format(name=name or 'друг')


def _has_active_subscription(profile: UserProfile) -> bool:
    from billing_app.trial_access import has_premium_access
    return has_premium_access(profile)


def _completed_lesson_ids(profile_id: int) -> set[int]:
    return set(
        LessonProgress.objects.filter(
            user_id=profile_id,
            status=LessonProgress.Status.COMPLETED,
        ).values_list('lesson_id', flat=True)
    )


def _active_lesson_ids(profile_id: int) -> set[int]:
    """Lessons done or placement-skipped — not offered again in the serial queue."""
    return set(
        LessonProgress.objects.filter(
            user_id=profile_id,
            status__in=(
                LessonProgress.Status.COMPLETED,
                LessonProgress.Status.SKIPPED,
            ),
        ).values_list('lesson_id', flat=True)
    )


def _lesson_queryset(profile: UserProfile, premium: bool):
    if premium:
        level = (profile.cefr_level or 'A1').lower()
        if level not in LEVEL_ORDER:
            level = 'a1'
        start = entry_level(profile)
        start_idx = LEVEL_ORDER.index(start) if start in LEVEL_ORDER else 0
        end_idx = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else start_idx
        allowed = LEVEL_ORDER[start_idx: end_idx + 1]
        return (
            Lesson.objects.filter(is_published=True, level__in=allowed)
            .select_related('unit')
            .order_by('unit__level', 'unit__order', 'order', 'id')
        )
    return (
        Lesson.objects.filter(is_published=True, is_trial=True)
        .select_related('unit')
        .order_by('unit__level', 'unit__order', 'order', 'id')
    )


def get_next_episode_lesson(profile: UserProfile) -> Lesson | None:
    apply_story_placement(profile)
    premium = _has_active_subscription(profile)
    done = _active_lesson_ids(profile.id)
    for lesson in _lesson_queryset(profile, premium):
        if lesson.id not in done:
            return lesson
    return None


def _due_words_count(profile_id: int) -> int:
    from progress_app.models import UserWordProgress

    now = timezone.now()
    return UserWordProgress.objects.filter(user_id=profile_id).filter(
        Q(next_review_at__lte=now) | Q(next_review_at__isnull=True),
    ).count()


def _interest_hint(profile: UserProfile) -> str:
    names = list(
        UserInterest.objects.filter(user=profile)
        .select_related('interest')
        .values_list('interest__name', flat=True)[:2]
    )
    custom = (profile.interests_custom or '').strip()
    if custom:
        first = custom.split(',')[0].strip()
        if first and first not in names:
            names.append(first)
    if not names:
        return ''
    return f' Сегодня с акцентом на: {", ".join(names[:2])}.'


def _schedule_hint(profile: UserProfile) -> str:
    minutes = effective_daily_minutes(profile)
    days = profile.study_days_per_week or 5
    return f' План: ~{minutes} мин · {days} дн/нед.'


def _episode_number(profile_id: int) -> int:
    return LessonProgress.objects.filter(
        user_id=profile_id,
        status=LessonProgress.Status.COMPLETED,
    ).count() + 1


def _purge_legacy_rules_blocks(session: DailySession) -> None:
    for block in session.blocks.all():
        if (block.content or {}).get('item_type') == 'rules':
            block.delete()


def _episode_block(session: DailySession) -> DailySessionBlock | None:
    for block in session.blocks.order_by('order'):
        if (block.content or {}).get('item_type') == 'episode':
            return block
    return None


def _block_exists(session: DailySession, item_type: str) -> bool:
    return any(
        (b.content or {}).get('item_type') == item_type
        for b in session.blocks.all()
    )


def _skill_focus_set(profile: UserProfile) -> set[str]:
    return set(profile.skill_focus or [])


def _include_listening(profile: UserProfile, minutes_budget: int) -> bool:
    if 'listening' in _skill_focus_set(profile):
        return minutes_budget >= 20
    return minutes_budget >= 30


def _include_speaking(profile: UserProfile, minutes_budget: int) -> bool:
    if profile.speaking_anxiety in ('high', 'mild'):
        return minutes_budget >= 20
    if 'speaking' in _skill_focus_set(profile):
        return minutes_budget >= 20
    return False


def _target_minutes_for_item(item: dict) -> int:
    item_type = item.get('type')
    if item_type == 'warmup':
        return WARMUP_MINUTES
    if item_type == 'episode':
        return int(item.get('minutes') or 8)
    if item_type == 'listening':
        return int(item.get('minutes') or LISTENING_MINUTES)
    if item_type == 'speaking':
        return int(item.get('minutes') or SPEAKING_MINUTES)
    if item_type == 'words':
        count = int(item.get('count') or 0)
        return max(2, min(count, 8))
    if item_type == 'rule_drill':
        return RULE_DRILL_MINUTES
    return 1


def _build_initial_blocks(
    session: DailySession,
    profile: UserProfile,
    fact: dict,
    *,
    day: date,
    rest: bool,
) -> None:
    """First visit of the day: warmup (+ episode & extras when not a rest day)."""
    order = 1
    icon, title = warmup_label(fact.get('kind', 'fact'))
    quiz = build_quiz_for_fact(
        {'fact_ru': fact['ru'], 'fact_en': fact['en'], 'kind': fact.get('kind', 'fact')},
        profile.id,
        day,
    )
    DailySessionBlock.objects.create(
        session=session,
        order=order,
        block_type=DailySessionBlock.BlockType.REFLECTION,
        title=title,
        content={
            'item_type': 'warmup',
            'kind': fact.get('kind', 'fact'),
            'fact_ru': fact['ru'],
            'fact_en': fact['en'],
            'quiz': quiz,
            'rest_day': rest,
        },
    )
    order += 1

    if rest:
        session.title = 'День отдыха'
        session.save(update_fields=['title', 'updated_at'])
        return

    minutes_budget = effective_daily_minutes(profile)
    episode = get_next_episode_lesson(profile)
    if episode:
        session.title = episode.title
        session.save(update_fields=['title', 'updated_at'])
        DailySessionBlock.objects.create(
            session=session,
            order=order,
            block_type=DailySessionBlock.BlockType.STORY,
            title=episode.title,
            content={
                'item_type': 'episode',
                'lesson_id': episode.id,
                'subtitle': episode.subtitle,
                'xp_reward': episode.xp_reward,
                'minutes': episode.estimated_minutes,
                'episode_num': _episode_number(profile.id),
            },
        )
        order += 1

    if _include_speaking(profile, minutes_budget) and not _block_exists(session, 'speaking'):
        bite = pick_speaking_bite(profile.id, day)
        DailySessionBlock.objects.create(
            session=session,
            order=order,
            block_type=DailySessionBlock.BlockType.DIALOGUE,
            title=bite['title'],
            content={
                'item_type': 'speaking',
                'title': bite['title'],
                'prompt_ru': bite['prompt_ru'],
                'prompt_en': bite['prompt_en'],
                'model_answer': bite['model_answer'],
                'keywords': bite.get('keywords', []),
                'minutes': bite.get('minutes', SPEAKING_MINUTES),
            },
        )
        order += 1

    if _include_listening(profile, minutes_budget) and not _block_exists(session, 'listening'):
        level = (profile.cefr_level or 'a2').lower()
        bite = pick_listening_bite(profile.id, day, user_level=level)
        DailySessionBlock.objects.create(
            session=session,
            order=order,
            block_type=DailySessionBlock.BlockType.DIALOGUE,
            title=bite['title'],
            content={
                'item_type': 'listening',
                'title': bite['title'],
                'lines': bite['lines'],
                'question_ru': bite['question_ru'],
                'options': bite['options'],
                'correct_index': bite['correct_index'],
                'minutes': bite.get('minutes', 4),
            },
        )
        order += 1

    if minutes_budget >= 60 and not _block_exists(session, 'rule_drill'):
        DailySessionBlock.objects.create(
            session=session,
            order=order,
            block_type=DailySessionBlock.BlockType.EXERCISE,
            title='Тренировка правил',
            content={'item_type': 'rule_drill'},
        )


def ensure_bonus_blocks(session: DailySession, profile: UserProfile) -> None:
    """After the main episode: optional word review."""
    if is_rest_day(profile, session.date):
        return
    ep = _episode_block(session)
    if not ep or not ep.is_completed:
        return
    if _block_exists(session, 'words'):
        return

    due = _due_words_count(profile.id)
    if not due:
        return

    max_order = max((b.order for b in session.blocks.all()), default=0)
    DailySessionBlock.objects.create(
        session=session,
        order=max_order + 1,
        block_type=DailySessionBlock.BlockType.VOCABULARY,
        title='Бонус: слова',
        content={'item_type': 'words', 'count': due},
    )


def _items_from_session(session: DailySession) -> list[dict]:
    items = []
    for block in session.blocks.order_by('order'):
        content = block.content or {}
        item_type = content.get('item_type', block.block_type)
        if item_type == 'rules':
            continue
        item = {
            'block_id': block.id,
            'type': item_type,
            'title': block.title,
            'done': block.is_completed,
            'lesson_id': content.get('lesson_id'),
            'count': content.get('count', 0),
            'kind': content.get('kind', 'fact'),
            'fact_ru': content.get('fact_ru', ''),
            'fact_en': content.get('fact_en', ''),
            'subtitle': content.get('subtitle', ''),
            'xp_reward': content.get('xp_reward', 0),
            'minutes': content.get('minutes', 0),
            'episode_num': content.get('episode_num', 0),
            'quiz': content.get('quiz'),
            'lines': content.get('lines'),
            'question_ru': content.get('question_ru', ''),
            'options': content.get('options'),
            'correct_index': content.get('correct_index'),
            'prompt_ru': content.get('prompt_ru', ''),
            'prompt_en': content.get('prompt_en', ''),
            'model_answer': content.get('model_answer', ''),
            'keywords': content.get('keywords', []),
            'rest_day': content.get('rest_day', False),
        }
        item['target_minutes'] = _target_minutes_for_item(item)
        items.append(item)
    return items


def _structured_plan(items: list[dict], *, daily_minutes: int) -> dict:
    warmup = next((i for i in items if i['type'] == 'warmup'), None)
    episode = next((i for i in items if i['type'] == 'episode'), None)
    listening = next((i for i in items if i['type'] == 'listening'), None)
    speaking = next((i for i in items if i['type'] == 'speaking'), None)
    bonus_words = next((i for i in items if i['type'] == 'words'), None)
    rule_drill = next((i for i in items if i['type'] == 'rule_drill'), None)

    route = [i for i in (warmup, episode, speaking, listening, bonus_words, rule_drill) if i]
    done_count = sum(1 for i in route if i.get('done'))
    total_count = len(route) or 1

    total_minutes = sum(i.get('target_minutes', 0) for i in route) or daily_minutes
    done_minutes = sum(i.get('target_minutes', 0) for i in route if i.get('done'))
    progress_percent = round(done_minutes / total_minutes * 100) if total_minutes else 0

    if warmup and not warmup.get('done'):
        continue_label = 'Начать'
    else:
        continue_label = 'Продолжить'

    return {
        'warmup': warmup,
        'episode': episode,
        'listening': listening,
        'speaking': speaking,
        'bonus_words': bonus_words,
        'rule_drill': rule_drill,
        'progress_done': done_count,
        'progress_total': total_count,
        'progress_percent': progress_percent,
        'progress_minutes_done': done_minutes,
        'progress_minutes_total': total_minutes,
        'continue_label': continue_label[:60],
    }


def build_or_get_daily_plan(profile: UserProfile, *, day: date | None = None) -> dict:
    """Create or refresh today's DailySession and return a plan dict for the bot."""
    day = day or timezone.localdate()
    premium = _has_active_subscription(profile)
    fact = _pick_fact(profile.id, day)
    rest = is_rest_day(profile, day)
    minutes = effective_daily_minutes(profile)
    greeting = _pick_greeting(profile.first_name, profile.id, day, rest=rest)
    interest_hint = _interest_hint(profile)
    schedule_hint = _schedule_hint(profile) if profile.study_schedule_set else ''

    session, created = DailySession.objects.get_or_create(
        user=profile,
        date=day,
        defaults={
            'title': 'День отдыха' if rest else 'Глава дня',
            'intro_text': greeting + interest_hint + schedule_hint,
            'status': DailySession.Status.PLANNED,
        },
    )

    if not created and session.status in {DailySession.Status.PLANNED, DailySession.Status.ACTIVE}:
        _purge_legacy_rules_blocks(session)

    if not session.blocks.exists():
        _build_initial_blocks(session, profile, fact, day=day, rest=rest)

    ensure_bonus_blocks(session, profile)

    items = _items_from_session(session)
    structured = _structured_plan(items, daily_minutes=minutes)

    from django.conf import settings

    trial_left = max(0, settings.TRIAL_LESSONS_LIMIT - profile.trial_lessons_used)

    return {
        'session_id': session.id,
        'date': day.isoformat(),
        'greeting': session.intro_text or greeting,
        'premium': premium,
        'trial_left': trial_left,
        'daily_minutes': minutes,
        'study_days_per_week': profile.study_days_per_week or 5,
        'is_rest_day': rest,
        'items': items,
        **structured,
        'all_done': bool(items) and all(i['done'] for i in items),
        'has_episode': structured.get('episode') is not None,
    }


def _display_title(title: str, fallback: str = '') -> str:
    """Plain block title for UI (strip icons if stored in older sessions)."""
    t = (title or fallback).strip()
    for prefix in ('🎧 ', '🎙️ ', '🎙 '):
        if t.startswith(prefix):
            return t[len(prefix):]
    return t


def format_plan_reminder_summary(plan: dict) -> str:
    """Short plain-text plan for daily reminder messages."""
    if plan.get('is_rest_day'):
        return '🌿 Сегодня день отдыха — лёгкая разминка (~5 мин). Серия дней не прервётся.'

    lines = ['📋 План на день:']
    step = 1
    warmup = plan.get('warmup')
    if warmup:
        from study_app.daily_facts import warmup_label
        icon, label = warmup_label(warmup.get('kind', 'fact'))
        mark = '✅' if warmup.get('done') else f'{step}.'
        lines.append(f'{mark} {icon} {label} — ~3 мин')
        step += 1
    episode = plan.get('episode')
    if episode:
        num = episode.get('episode_num')
        title = episode.get('subtitle') or episode.get('title', 'Эпизод')
        mins = episode.get('minutes') or 8
        xp = episode.get('xp_reward') or 0
        mark = '✅' if episode.get('done') else f'{step}.'
        meta = f'~{mins} мин'
        if xp:
            meta += f' · +{xp} XP'
        if num:
            lines.append(f'{mark} 📺 Эпизод {num}: {title} — {meta}')
        else:
            lines.append(f'{mark} 📺 {title} — {meta}')
        step += 1
    elif not plan.get('has_episode'):
        lines.append('📚 Сегодня без эпизода — новая глава скоро в программе')
    listening = plan.get('listening')
    if listening:
        mark = '✅' if listening.get('done') else f'{step}.'
        title = _display_title(listening.get('title', ''), 'Аудирование')
        lines.append(f'{mark} 🎧 {title} — ~{listening.get("target_minutes", 4)} мин')
        step += 1
    speaking = plan.get('speaking')
    if speaking:
        mark = '✅' if speaking.get('done') else f'{step}.'
        title = _display_title(speaking.get('title', ''), 'Говорение')
        lines.append(f'{mark} 🎙 {title} — ~{speaking.get("target_minutes", 4)} мин')
        step += 1
    bonus = plan.get('bonus_words')
    if bonus:
        mark = '✅' if bonus.get('done') else f'{step}.'
        lines.append(f'{mark} 🗂 Повторить {bonus.get("count", 0)} слов')
        step += 1
    drill = plan.get('rule_drill')
    if drill:
        mark = '✅' if drill.get('done') else f'{step}.'
        lines.append(f'{mark} 📖 Тренировка правил — ~5 мин')
    pct = plan.get('progress_percent', 0)
    total_m = plan.get('progress_minutes_total', 0)
    if total_m:
        lines.append(f'≈ {pct}% · ~{total_m} мин на сегодня')
    return '\n'.join(lines)
