"""Build a personalized daily training plan (adventure chapter) per learner."""

from __future__ import annotations

import hashlib
from datetime import date

from django.db.models import Q
from django.utils import timezone

from content_app.models import Lesson
from study_app.daily_facts import DAILY_FACTS, GREETING_VARIANTS, warmup_label
from study_app.models import DailySession, DailySessionBlock, LessonProgress
from users_app.models import UserInterest, UserProfile

LEVEL_ORDER = ['a1', 'a2', 'b1', 'b2']


def _day_seed(user_id: int, day: date) -> int:
    raw = f'{user_id}:{day.isoformat()}'.encode()
    return int(hashlib.sha256(raw).hexdigest(), 16)


def _pick_fact(user_id: int, day: date) -> dict:
    idx = _day_seed(user_id, day) % len(DAILY_FACTS)
    return DAILY_FACTS[idx]


def _pick_greeting(name: str, user_id: int, day: date) -> str:
    idx = (_day_seed(user_id, day) // 7) % len(GREETING_VARIANTS)
    return GREETING_VARIANTS[idx].format(name=name or 'друг')


def _has_active_subscription(profile: UserProfile) -> bool:
    from billing_app.models import Subscription

    return Subscription.objects.filter(
        user=profile,
        status=Subscription.Status.ACTIVE,
        expires_at__gt=timezone.now(),
    ).exists()


def _completed_lesson_ids(profile_id: int) -> set[int]:
    return set(
        LessonProgress.objects.filter(
            user_id=profile_id,
            status=LessonProgress.Status.COMPLETED,
        ).values_list('lesson_id', flat=True)
    )


def _lesson_queryset(profile: UserProfile, premium: bool):
    if premium:
        level = (profile.cefr_level or 'A1').lower()
        if level not in LEVEL_ORDER:
            level = 'a1'
        allowed = LEVEL_ORDER[: LEVEL_ORDER.index(level) + 1]
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
    premium = _has_active_subscription(profile)
    completed = _completed_lesson_ids(profile.id)
    for lesson in _lesson_queryset(profile, premium):
        if lesson.id not in completed:
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
    if not names:
        return ''
    return f' Сегодня с акцентом на: {", ".join(names)}.'


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


def _build_initial_blocks(session: DailySession, profile: UserProfile, fact: dict) -> None:
    """First visit of the day: warmup + pinned episode (no rules checklist)."""
    order = 1
    icon, title = warmup_label(fact.get('kind', 'fact'))
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
        },
    )
    order += 1

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


def ensure_bonus_blocks(session: DailySession, profile: UserProfile) -> None:
    """After the main episode: optional word review (rules live in 📖 Правила)."""
    ep = _episode_block(session)
    if not ep or not ep.is_completed:
        return

    for block in session.blocks.all():
        if (block.content or {}).get('item_type') == 'words':
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
        items.append({
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
        })
    return items


def _structured_plan(items: list[dict]) -> dict:
    warmup = next((i for i in items if i['type'] == 'warmup'), None)
    episode = next((i for i in items if i['type'] == 'episode'), None)
    bonus_words = next((i for i in items if i['type'] == 'words'), None)

    required = [i for i in (warmup, episode) if i]
    if bonus_words:
        required.append(bonus_words)
    done_count = sum(1 for i in required if i.get('done'))
    total = len(required) or 1

    if episode and not episode.get('done'):
        continue_label = 'Продолжить'
    elif bonus_words and not bonus_words.get('done'):
        continue_label = 'Продолжить'
    elif warmup and not warmup.get('done'):
        continue_label = 'Начать'
    else:
        continue_label = 'Продолжить'

    return {
        'warmup': warmup,
        'episode': episode,
        'bonus_words': bonus_words,
        'progress_done': done_count,
        'progress_total': total,
        'continue_label': continue_label[:60],
    }


def build_or_get_daily_plan(profile: UserProfile, *, day: date | None = None) -> dict:
    """Create or refresh today's DailySession and return a plan dict for the bot."""
    day = day or timezone.localdate()
    premium = _has_active_subscription(profile)
    fact = _pick_fact(profile.id, day)
    greeting = _pick_greeting(profile.first_name, profile.id, day)
    interest_hint = _interest_hint(profile)

    session, created = DailySession.objects.get_or_create(
        user=profile,
        date=day,
        defaults={
            'title': 'Глава дня',
            'intro_text': greeting + interest_hint,
            'status': DailySession.Status.PLANNED,
        },
    )

    if not created and session.status in {DailySession.Status.PLANNED, DailySession.Status.ACTIVE}:
        _purge_legacy_rules_blocks(session)

    if not session.blocks.exists():
        _build_initial_blocks(session, profile, fact)

    ensure_bonus_blocks(session, profile)

    items = _items_from_session(session)
    structured = _structured_plan(items)

    from django.conf import settings

    trial_left = max(0, settings.TRIAL_LESSONS_LIMIT - profile.trial_lessons_used)

    return {
        'session_id': session.id,
        'date': day.isoformat(),
        'greeting': session.intro_text or greeting,
        'premium': premium,
        'trial_left': trial_left,
        'items': items,
        **structured,
        'all_done': bool(items) and all(i['done'] for i in items),
        'has_episode': structured.get('episode') is not None,
    }


def format_plan_reminder_summary(plan: dict) -> str:
    """Short plain-text plan for daily reminder messages."""
    lines = ['📋 План на день:']
    step = 1
    warmup = plan.get('warmup')
    if warmup:
        from study_app.daily_facts import warmup_label
        icon, label = warmup_label(warmup.get('kind', 'fact'))
        mark = '✅' if warmup.get('done') else f'{step}.'
        lines.append(f'{mark} {icon} {label} — ~1 мин')
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
        lines.append('🎬 Новая глава скоро')
    bonus = plan.get('bonus_words')
    if bonus:
        mark = '✅' if bonus.get('done') else f'{step}.'
        lines.append(f'{mark} 🗂 Повторить {bonus.get("count", 0)} слов')
    return '\n'.join(lines)
