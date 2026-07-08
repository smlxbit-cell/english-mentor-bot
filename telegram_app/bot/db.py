"""Async-friendly database access for the bot.

Every function is wrapped with sync_to_async and returns plain dicts / lists so
the async handlers never touch lazy ORM objects across the async boundary.
"""

from __future__ import annotations

from datetime import timedelta

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from billing_app.models import Payment, Subscription, SubscriptionPlan
from content_app.level_variants import apply_level_variants
from content_app.models import DiagnosticItem, Lesson, LessonStep
from gamification_app.models import Achievement, UserAchievement, UserStats
from users_app.models import Interest, UserInterest, UserProfile

LEVELS = ['a1', 'a2', 'b1', 'b2']
PLAN_CODE = 'basic'
XP_PER_LEVEL = 100

SKILL_RU = {
    'grammar': 'грамматика', 'vocabulary': 'лексика',
    'listening': 'аудирование', 'reading': 'чтение',
    'speaking': 'говорение', 'pronunciation': 'произношение',
    'writing': 'письмо', 'mixed': 'общее',
}

# English topic hints for AI personalization, keyed by profession/sphere code.
SPHERE_EN = {
    'ecommerce': 'e-commerce and online stores',
    'it': 'IT and software development',
    'hospitality': 'hotels and tourism',
    'food': 'cafes and restaurants',
    'education': 'teaching and education',
    'psychology': 'psychology',
    'medicine': 'healthcare and medicine',
    'finance': 'finance and banking',
    'marketing': 'marketing and advertising',
    'design': 'design and creative work',
    'law': 'law and legal services',
    'logistics': 'logistics and supply chain',
    'student': 'studying (not working yet)',
    'other': '',
}


def sphere_display_label(profession: str, profession_custom: str = '') -> str:
    if profession == 'other' and profession_custom:
        return profession_custom
    return dict(UserProfile.Sphere.choices).get(profession, '')


def sphere_topic(profession: str, profession_custom: str = '') -> str:
    if profession == 'other' and profession_custom:
        return profession_custom.strip()
    return SPHERE_EN.get(profession or '', '')

GOAL_EN = {
    'travel': 'travel',
    'work': 'work and career',
    'study': 'studying',
    'movies': 'movies and TV series',
    'relocation': 'moving abroad',
    'communication': 'everyday communication',
    'exams': 'English exams',
    'personal': 'personal growth and self-development',
}


def personalization_topic(
    learning_goal: str,
    learning_goal_custom: str = '',
    profession: str = '',
    profession_custom: str = '',
    interest_names: list[str] | None = None,
) -> str:
    """English context string for AI exercises (goal + interests + sphere)."""
    parts: list[str] = []
    if learning_goal == 'other' and learning_goal_custom:
        parts.append(learning_goal_custom.strip())
    elif learning_goal and learning_goal in GOAL_EN:
        parts.append(GOAL_EN[learning_goal])
    if interest_names:
        parts.append('interests: ' + ', '.join(interest_names[:8]))
    sphere = sphere_topic(profession, profession_custom)
    if sphere:
        parts.append(sphere)
    return '; '.join(parts)


def parse_custom_interests(text: str) -> list[str]:
    return [p.strip() for p in (text or '').split(',') if p.strip()]


def all_interest_names(
    profile_id: int,
    *,
    preset_names: list[str] | None = None,
    interests_custom: str = '',
) -> list[str]:
    names = list(preset_names or [])
    names.extend(parse_custom_interests(interests_custom))
    return names


def goal_display_label(learning_goal: str, learning_goal_custom: str = '') -> str:
    if learning_goal == 'other' and learning_goal_custom:
        return learning_goal_custom
    return dict(UserProfile.LearningGoal.choices).get(learning_goal, '')


def onboarding_state(profile: UserProfile) -> dict:
    """Which onboarding step is missing before lessons can start."""
    if not profile.diagnostic_completed:
        return {'complete': False, 'step': 'diagnostic'}
    if not profile.learning_goal:
        return {'complete': False, 'step': 'goal'}
    has_preset = UserInterest.objects.filter(user_id=profile.id).exists()
    has_custom = bool(parse_custom_interests(profile.interests_custom))
    if not has_preset and not has_custom:
        return {'complete': False, 'step': 'interests'}
    if not profile.profession:
        return {'complete': False, 'step': 'sphere'}
    if profile.profession == 'other' and not (profile.profession_custom or '').strip():
        return {'complete': False, 'step': 'sphere'}
    if not profile.study_schedule_set:
        if not profile.target_cefr_level:
            return {'complete': False, 'step': 'target_level'}
        if not profile.skill_focus_confirmed:
            return {'complete': False, 'step': 'skill_focus'}
        return {'complete': False, 'step': 'schedule'}
    return {'complete': True, 'step': 'done'}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _has_active_subscription(profile_id: int) -> bool:
    from billing_app.trial_access import has_premium_access
    profile = UserProfile.objects.get(id=profile_id)
    return has_premium_access(profile)


def _media_dict(media) -> dict | None:
    if not media:
        return None
    return {
        'id': media.id,
        'media_type': media.media_type,
        'telegram_file_id': media.telegram_file_id or '',
        'source_url': media.source_url or '',
        'file': media.file.name if media.file else '',
        'title': media.title,
    }


def _profile_dict(profile: UserProfile) -> dict:
    preset_interests = list(
        UserInterest.objects.filter(user_id=profile.id)
        .select_related('interest')
        .values_list('interest__name', flat=True)
    )
    interest_names = all_interest_names(
        profile.id,
        preset_names=preset_interests,
        interests_custom=profile.interests_custom or '',
    )
    onboarding = onboarding_state(profile)
    return {
        'id': profile.id,
        'telegram_id': profile.telegram_id,
        'first_name': profile.first_name or '',
        'cefr_level': profile.cefr_level or '',
        'level_code': (profile.cefr_level or '').lower() or 'a1',
        'diagnostic_completed': profile.diagnostic_completed,
        'trial_lessons_used': profile.trial_lessons_used,
        'trial_limit': settings.TRIAL_LESSONS_LIMIT,
        'weak_skills': profile.weak_skills or [],
        'profession': profile.profession or '',
        'sphere_en': sphere_topic(
            profile.profession or '', profile.profession_custom or '',
        ),
        'learning_goal': profile.learning_goal or '',
        'interests_custom': profile.interests_custom or '',
        'onboarding_complete': onboarding['complete'],
        'onboarding_step': onboarding['step'],
        'daily_minutes': profile.daily_minutes or 20,
        'study_days_per_week': profile.study_days_per_week or 5,
        'rest_weekday': profile.rest_weekday if profile.rest_weekday is not None else 6,
        'study_schedule_set': profile.study_schedule_set,
        'target_cefr_level': profile.target_cefr_level or '',
        'skill_focus': profile.skill_focus or [],
        'personalization_topic': personalization_topic(
            profile.learning_goal or '',
            profile.learning_goal_custom or '',
            profile.profession or '',
            profile.profession_custom or '',
            interest_names=interest_names,
        ),
        'is_premium': _has_active_subscription(profile.id),
    }


# --------------------------------------------------------------------------- #
# Profile
# --------------------------------------------------------------------------- #

@sync_to_async
def get_or_create_profile(tg_user) -> dict:
    profile, created = UserProfile.objects.get_or_create(
        telegram_id=tg_user.id,
        defaults={
            'telegram_username': tg_user.username or '',
            'first_name': tg_user.first_name or '',
            'last_name': tg_user.last_name or '',
        },
    )
    previous_last_seen = None if created else profile.last_seen
    profile.telegram_username = tg_user.username or ''
    profile.first_name = tg_user.first_name or ''
    profile.last_name = tg_user.last_name or ''
    profile.last_seen = timezone.now()
    profile.save(update_fields=[
        'telegram_username', 'first_name', 'last_name', 'last_seen', 'updated_at',
    ])
    UserStats.objects.get_or_create(user=profile)
    data = _profile_dict(profile)
    data['previous_last_seen'] = previous_last_seen
    return data


@sync_to_async
def get_profile(profile_id: int) -> dict:
    return _profile_dict(UserProfile.objects.get(id=profile_id))


@sync_to_async
def get_profile_detail(profile_id: int) -> dict:
    from study_app.models import LessonProgress

    profile = UserProfile.objects.get(id=profile_id)
    stats, _ = UserStats.objects.get_or_create(user=profile)

    completed = LessonProgress.objects.filter(
        user_id=profile.id, status=LessonProgress.Status.COMPLETED,
    ).count()
    sub = Subscription.objects.filter(
        user_id=profile.id, status=Subscription.Status.ACTIVE,
        expires_at__gt=timezone.now(),
    ).order_by('-expires_at').first()

    interests = list(
        UserInterest.objects.filter(user_id=profile.id)
        .select_related('interest')
        .values_list('interest__name', flat=True)
    )
    interests.extend(parse_custom_interests(profile.interests_custom))

    achievements = []
    unlocked_ids = set(
        UserAchievement.objects.filter(user_id=profile.id)
        .values_list('achievement_id', flat=True)
    )
    for ach in Achievement.objects.filter(is_active=True).order_by('title'):
        achievements.append({
            'title': ach.title,
            'icon': ach.icon or '🏆',
            'unlocked': ach.id in unlocked_ids,
        })

    xp_into_level = stats.xp_total % XP_PER_LEVEL
    xp_to_next = XP_PER_LEVEL - xp_into_level

    goal_label = goal_display_label(
        profile.learning_goal or '',
        profile.learning_goal_custom or '',
    )
    sphere_label = sphere_display_label(
        profile.profession or '', profile.profession_custom or '',
    )

    from billing_app.limits import get_user_limits, voice_remaining_minutes

    limits = get_user_limits(profile)
    plan_name = limits['plan_name']
    if limits['has_subscription'] and sub:
        plan_name = sub.plan.name

    return {
        'first_name': profile.first_name or '',
        'level': (profile.cefr_level or '').upper() or 'не определён',
        'goal': goal_label,
        'sphere': sphere_label,
        'interests': interests,
        'weak_skills_ru': [SKILL_RU.get(s, s) for s in (profile.weak_skills or [])],
        'xp': stats.xp_total,
        'user_level': stats.level,
        'xp_to_next': xp_to_next,
        'streak': stats.current_streak,
        'longest_streak': stats.longest_streak,
        'completed_lessons': completed,
        'trial_used': profile.trial_lessons_used,
        'trial_limit': settings.TRIAL_LESSONS_LIMIT,
        'premium': _has_active_subscription(profile.id),
        'subscription_until': sub.expires_at.strftime('%d.%m.%Y') if sub else None,
        'plan_name': plan_name,
        'plan_code': limits['plan_code'],
        'voice_remaining_minutes': voice_remaining_minutes(profile),
        'voice_minutes_monthly': limits['voice_minutes_monthly'],
        'tutor_ai_monthly_limit': limits['tutor_ai_monthly_limit'],
        'tutor_messages_remaining': limits['tutor_messages_remaining'],
        'daily_minutes': profile.daily_minutes or 20,
        'study_days_per_week': profile.study_days_per_week or 5,
        'target_cefr_level': profile.target_cefr_level or '',
        'skill_focus_ru': [SKILL_RU.get(s, s) for s in (profile.skill_focus or [])],
        'achievements': achievements,
    }


# --------------------------------------------------------------------------- #
# Interests & goal
# --------------------------------------------------------------------------- #

@sync_to_async
def get_interests_custom(profile_id: int) -> str:
    return UserProfile.objects.filter(id=profile_id).values_list(
        'interests_custom', flat=True,
    ).first() or ''


@sync_to_async
def set_interests_custom(profile_id: int, text: str) -> None:
    UserProfile.objects.filter(id=profile_id).update(
        interests_custom=(text or '')[:500],
    )


@sync_to_async
def clear_user_interests(profile_id: int) -> None:
    UserInterest.objects.filter(user_id=profile_id).delete()
    UserProfile.objects.filter(id=profile_id).update(interests_custom='')


@sync_to_async
def complete_onboarding(profile_id: int) -> None:
    UserProfile.objects.filter(id=profile_id).update(
        onboarding_status=UserProfile.OnboardingStatus.COMPLETED,
    )


@sync_to_async
def set_target_cefr_level(profile_id: int, level_code: str) -> None:
    allowed = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
    code = (level_code or '').upper()
    if code in allowed:
        UserProfile.objects.filter(id=profile_id).update(target_cefr_level=code)


@sync_to_async
def get_target_cefr_level(profile_id: int) -> str:
    return UserProfile.objects.filter(id=profile_id).values_list(
        'target_cefr_level', flat=True,
    ).first() or ''


FOCUS_SKILLS = ['speaking', 'listening', 'reading', 'writing', 'grammar', 'vocabulary']


@sync_to_async
def confirm_skill_focus(profile_id: int) -> None:
    UserProfile.objects.filter(id=profile_id).update(skill_focus_confirmed=True)


@sync_to_async
def set_skill_focus_list(profile_id: int, skills: list[str]) -> None:
    """Replace the skill-focus list (e.g. from the deep skill-assessment)."""
    clean = [s for s in (skills or []) if s in FOCUS_SKILLS][:6]
    UserProfile.objects.filter(id=profile_id).update(skill_focus=clean)


@sync_to_async
def set_speaking_anxiety(profile_id: int, level: str) -> None:
    allowed = {'high', 'mild', 'none'}
    code = (level or '').lower()
    if code not in allowed:
        return
    profile = UserProfile.objects.get(id=profile_id)
    profile.speaking_anxiety = code
    profile.save(update_fields=['speaking_anxiety', 'updated_at'])
    if code in ('high', 'mild'):
        focus = list(profile.skill_focus or [])
        if 'speaking' not in focus:
            focus.insert(0, 'speaking')
            profile.skill_focus = focus[:6]
            profile.save(update_fields=['skill_focus', 'updated_at'])


@sync_to_async
def ensure_skill_in_focus(profile_id: int, skill: str) -> None:
    if skill not in FOCUS_SKILLS:
        return
    profile = UserProfile.objects.get(id=profile_id)
    focus = list(profile.skill_focus or [])
    if skill not in focus:
        focus.append(skill)
        profile.skill_focus = focus[:6]
        profile.save(update_fields=['skill_focus', 'updated_at'])


@sync_to_async
def toggle_skill_focus(profile_id: int, skill: str) -> list[str]:
    if skill not in FOCUS_SKILLS:
        return []
    profile = UserProfile.objects.get(id=profile_id)
    focus = list(profile.skill_focus or [])
    if skill in focus:
        focus.remove(skill)
    else:
        focus.append(skill)
    profile.skill_focus = focus[:6]
    profile.save(update_fields=['skill_focus', 'updated_at'])
    return profile.skill_focus


@sync_to_async
def get_skill_focus(profile_id: int) -> list[str]:
    return list(UserProfile.objects.filter(id=profile_id).values_list(
        'skill_focus', flat=True,
    ).first() or [])


@sync_to_async
def set_study_schedule(
    profile_id: int,
    *,
    daily_minutes: int,
    study_days_per_week: int,
    rest_weekday: int | None = None,
) -> None:
    minutes = daily_minutes if daily_minutes in (20, 30, 60) else 20
    days = max(3, min(7, study_days_per_week))
    fields = dict(
        daily_minutes=minutes,
        study_days_per_week=days,
        study_schedule_set=True,
    )
    if rest_weekday is not None:
        # 0–6 = weekday, 7 = no fixed rest day.
        fields['rest_weekday'] = max(0, min(7, rest_weekday))
    UserProfile.objects.filter(id=profile_id).update(**fields)


@sync_to_async
def get_study_schedule(profile_id: int) -> dict:
    profile = UserProfile.objects.get(id=profile_id)
    return {
        'daily_minutes': profile.daily_minutes or 20,
        'study_days_per_week': profile.study_days_per_week or 5,
        'rest_weekday': profile.rest_weekday if profile.rest_weekday is not None else 6,
        'study_schedule_set': profile.study_schedule_set,
    }


@sync_to_async
def has_any_interests(profile_id: int) -> bool:
    profile = UserProfile.objects.get(id=profile_id)
    if UserInterest.objects.filter(user_id=profile_id).exists():
        return True
    return bool(parse_custom_interests(profile.interests_custom))


# Curated interest order for the picker (slug from slugify(name, allow_unicode=True)).
INTEREST_ORDER = [
    'путешествия', 'кино-и-сериалы', 'музыка', 'игры', 'спорт', 'книги',
    'искусство', 'природа', 'работа-и-карьера', 'бизнес', 'технологии', 'наука',
    'еда-и-кухня', 'мода', 'психология', 'история',
]


@sync_to_async
def get_interests() -> list[dict]:
    by_slug = {
        i.slug: {'id': i.id, 'name': i.name, 'slug': i.slug}
        for i in Interest.objects.all()
    }
    ordered: list[dict] = []
    seen: set[str] = set()
    for slug in INTEREST_ORDER:
        if slug in by_slug:
            ordered.append(by_slug[slug])
            seen.add(slug)
    for slug in sorted(by_slug):
        if slug not in seen:
            ordered.append(by_slug[slug])
    return ordered


@sync_to_async
def get_user_interest_ids(profile_id: int) -> list[int]:
    return list(
        UserInterest.objects.filter(user_id=profile_id)
        .values_list('interest_id', flat=True)
    )


@sync_to_async
def toggle_interest(profile_id: int, interest_id: int) -> list[int]:
    existing = UserInterest.objects.filter(user_id=profile_id, interest_id=interest_id)
    if existing.exists():
        existing.delete()
    else:
        UserInterest.objects.get_or_create(user_id=profile_id, interest_id=interest_id)
    return list(
        UserInterest.objects.filter(user_id=profile_id)
        .values_list('interest_id', flat=True)
    )


@sync_to_async
def clear_learning_goal(profile_id: int) -> None:
    UserProfile.objects.filter(id=profile_id).update(
        learning_goal='', learning_goal_custom='',
    )


@sync_to_async
def set_learning_goal(
    profile_id: int, goal_code: str, custom_text: str = '',
) -> None:
    updates = {'learning_goal': goal_code}
    if goal_code == 'other':
        updates['learning_goal_custom'] = (custom_text or '')[:200]
    else:
        updates['learning_goal_custom'] = ''
    UserProfile.objects.filter(id=profile_id).update(**updates)


@sync_to_async
def clear_profession(profile_id: int) -> None:
    UserProfile.objects.filter(id=profile_id).update(
        profession='', profession_custom='',
    )


@sync_to_async
def set_profession(
    profile_id: int, sphere_code: str, custom_text: str = '',
) -> None:
    updates = {'profession': sphere_code}
    if sphere_code == 'other':
        updates['profession_custom'] = (custom_text or '')[:200]
    else:
        updates['profession_custom'] = ''
    UserProfile.objects.filter(id=profile_id).update(**updates)


def learning_goal_choices() -> list[dict]:
    return [{'code': c, 'label': lbl} for c, lbl in UserProfile.LearningGoal.choices]


def sphere_choices() -> list[dict]:
    return [{'code': c, 'label': lbl} for c, lbl in UserProfile.Sphere.choices]


# --------------------------------------------------------------------------- #
# Diagnostic
# --------------------------------------------------------------------------- #

@sync_to_async
def get_diagnostic_items() -> list[dict]:
    items = []
    for item in DiagnosticItem.objects.filter(is_active=True).order_by('level', 'order'):
        items.append({
            'id': item.id,
            'level': item.level,
            'skill': item.skill,
            'item_type': item.item_type,
            'prompt': item.prompt,
            'options': item.options or [],
            'correct': item.correct or [],
            'keywords': item.keywords or [],
            'explanation_ru': item.explanation_ru or '',
            'audio': _media_dict(item.audio),
        })
    return items


@sync_to_async
def finish_diagnostic(profile_id: int, level_code: str, weak_skills: list[str]) -> None:
    profile = UserProfile.objects.get(id=profile_id)
    profile.cefr_level = level_code.upper()
    profile.diagnostic_completed = True
    profile.trial_lessons_used = 0
    profile.weak_skills = weak_skills
    if profile.onboarding_status == UserProfile.OnboardingStatus.NOT_STARTED:
        profile.onboarding_status = UserProfile.OnboardingStatus.IN_PROGRESS
    profile.save()


@sync_to_async
def reset_diagnostic(profile_id: int) -> None:
    profile = UserProfile.objects.get(id=profile_id)
    profile.diagnostic_completed = False
    profile.trial_lessons_used = 0
    profile.save(update_fields=['diagnostic_completed', 'trial_lessons_used', 'updated_at'])


# --------------------------------------------------------------------------- #
# Lessons
# --------------------------------------------------------------------------- #

def _rank_lessons(profile, qs, completed_ids):
    """Order lessons by personalization: incomplete first, then weak-skill and
    interest match, then authored order. Returns list of dicts + marks the top
    incomplete lesson as recommended."""
    weak = set(profile.weak_skills or [])
    interest_names = {
        n.lower() for n in all_interest_names(
            profile.id,
            preset_names=list(
                UserInterest.objects.filter(user_id=profile.id)
                .select_related('interest')
                .values_list('interest__name', flat=True)
            ),
            interests_custom=profile.interests_custom or '',
        )
    }

    scored = []
    for lesson in qs:
        step_skills = set(
            lesson.steps.values_list('skill', flat=True)
        )
        tags = {str(t).lower() for t in (lesson.tags or [])}

        weak_hits = len(step_skills & weak)
        interest_hits = len(tags & interest_names)
        score = weak_hits * 2 + interest_hits
        completed = lesson.id in completed_ids
        scored.append({
            'lesson': lesson,
            'completed': completed,
            'score': score,
        })

    # Incomplete first, then higher score, then authored order.
    scored.sort(key=lambda s: (
        s['completed'], -s['score'], s['lesson'].order, s['lesson'].id,
    ))

    lessons = []
    recommended_marked = False
    for s in scored:
        lesson = s['lesson']
        recommended = False
        if not s['completed'] and not recommended_marked:
            recommended = True
            recommended_marked = True
        lessons.append({
            'id': lesson.id,
            'title': lesson.title,
            'subtitle': lesson.subtitle,
            'is_trial': lesson.is_trial,
            'completed': s['completed'],
            'recommended': recommended,
            'xp_reward': lesson.xp_reward,
        })
    return lessons


@sync_to_async
def get_available_lessons(profile_id: int) -> dict:
    profile = UserProfile.objects.get(id=profile_id)
    level = (profile.cefr_level or 'A1').lower()
    premium = _has_active_subscription(profile.id)

    from study_app.models import LessonProgress

    completed_ids = set(
        LessonProgress.objects.filter(
            user_id=profile.id, status=LessonProgress.Status.COMPLETED,
        ).values_list('lesson_id', flat=True)
    )

    qs = Lesson.objects.filter(
        level=level, is_published=True,
    ).prefetch_related('steps').order_by('order', 'id')
    if not qs.exists():
        # Fallback so the trial funnel always has something to show.
        qs = Lesson.objects.filter(
            is_published=True, is_trial=True,
        ).prefetch_related('steps').order_by('level', 'order', 'id')

    lessons = _rank_lessons(profile, qs, completed_ids)

    return {
        'level': level,
        'premium': premium,
        'trial_used': profile.trial_lessons_used,
        'trial_limit': settings.TRIAL_LESSONS_LIMIT,
        'lessons': lessons,
    }


@sync_to_async
def get_lesson_flow(lesson_id: int, *, profile_id: int | None = None) -> dict | None:
    try:
        lesson = Lesson.objects.select_related('character').get(id=lesson_id)
    except Lesson.DoesNotExist:
        return None

    user_level = lesson.level
    if profile_id:
        profile = UserProfile.objects.filter(id=profile_id).values_list(
            'cefr_level', flat=True,
        ).first()
        if profile:
            user_level = profile.lower()

    character = None
    if lesson.character:
        character = {
            'name': lesson.character.name,
            'role': lesson.character.role,
            'personality': lesson.character.personality,
            'speaking_style': lesson.character.speaking_style,
            'video_note_file_id': lesson.character.video_note_file_id,
        }

    steps = []
    for step in lesson.steps.select_related('media', 'character').order_by('order'):
        step_char = None
        if step.character:
            step_char = {
                'name': step.character.name,
                'role': step.character.role,
                'personality': step.character.personality,
                'speaking_style': step.character.speaking_style,
                'video_note_file_id': step.character.video_note_file_id,
            }
        steps.append({
            'id': step.id,
            'order': step.order,
            'step_type': step.step_type,
            'title': step.title,
            'text': step.text,
            'skill': step.skill,
            'content': step.content or {},
            'xp_reward': step.xp_reward,
            'media': _media_dict(step.media),
            'character': step_char,
        })

    steps = apply_level_variants(steps, user_level)

    return {
        'id': lesson.id,
        'title': lesson.title,
        'subtitle': lesson.subtitle,
        'level': lesson.level,
        'is_trial': lesson.is_trial,
        'intro_text': lesson.intro_text,
        'outro_text': lesson.outro_text,
        'xp_reward': lesson.xp_reward,
        'character': character,
        'steps': steps,
    }


def placement_note_for_profile(profile_id: int) -> str | None:
    from study_app.services.daily_plan import get_next_episode_lesson
    from study_app.services.episode_routing import placement_episode_title, placement_message

    profile = UserProfile.objects.get(id=profile_id)
    title = placement_episode_title(profile)
    if not title:
        return None
    nxt = get_next_episode_lesson(profile)
    if nxt and nxt.title == title:
        return placement_message(title, profile.cefr_level or 'B2')
    return None


placement_note_for_profile = sync_to_async(placement_note_for_profile)


@sync_to_async
def can_start_lesson(profile_id: int, lesson_id: int) -> dict:
    from billing_app.trial_access import has_premium_access

    profile = UserProfile.objects.get(id=profile_id)
    lesson = Lesson.objects.get(id=lesson_id)
    premium = has_premium_access(profile)

    from study_app.models import LessonProgress

    already_completed = LessonProgress.objects.filter(
        user_id=profile.id, lesson_id=lesson.id,
        status=LessonProgress.Status.COMPLETED,
    ).exists()

    # 2-day full trial (or active subscription) opens the whole app.
    # After it ends, everything is behind the paywall.
    if premium or already_completed:
        return {'allowed': True, 'premium': premium}

    return {'allowed': False, 'reason': 'paywall', 'premium': premium}


@sync_to_async
def start_or_resume_lesson(profile_id: int, lesson_id: int) -> dict:
    from study_app.models import LessonProgress

    progress, _ = LessonProgress.objects.get_or_create(
        user_id=profile_id, lesson_id=lesson_id,
    )
    if progress.status == LessonProgress.Status.COMPLETED:
        progress.status = LessonProgress.Status.IN_PROGRESS
        progress.current_step_index = 0
        progress.correct_count = 0
        progress.total_answered = 0
        progress.xp_earned = 0
        progress.completed_at = None
        progress.save()
    return {
        'id': progress.id,
        'current_step_index': progress.current_step_index,
    }


@sync_to_async
def save_step_index(profile_id: int, lesson_id: int, index: int) -> None:
    from study_app.models import LessonProgress

    LessonProgress.objects.filter(
        user_id=profile_id, lesson_id=lesson_id,
    ).update(current_step_index=index)


@sync_to_async
def record_attempt(profile_id: int, lesson_id: int, step_id: int, answer_text: str,
                   result: dict) -> None:
    from study_app.models import LessonProgress, StepAttempt

    StepAttempt.objects.create(
        user_id=profile_id,
        lesson_id=lesson_id,
        step_id=step_id,
        answer_text=answer_text[:2000],
        is_correct=bool(result.get('is_correct')),
        score=float(result.get('score', 0.0) or 0.0),
        used_ai=bool(result.get('used_ai')),
        method=result.get('method', '')[:30],
        feedback=result.get('feedback_ru', ''),
    )
    progress = LessonProgress.objects.filter(
        user_id=profile_id, lesson_id=lesson_id,
    ).first()
    if progress:
        progress.total_answered += 1
        if result.get('is_correct'):
            progress.correct_count += 1
        progress.save(update_fields=['total_answered', 'correct_count'])


@sync_to_async
def complete_lesson(profile_id: int, lesson_id: int) -> dict:
    from study_app.models import LessonProgress

    profile = UserProfile.objects.get(id=profile_id)
    lesson = Lesson.objects.get(id=lesson_id)
    premium = _has_active_subscription(profile.id)

    progress = LessonProgress.objects.filter(
        user_id=profile.id, lesson_id=lesson.id,
    ).first()
    was_completed = progress and progress.status == LessonProgress.Status.COMPLETED

    xp = lesson.xp_reward
    if progress:
        progress.status = LessonProgress.Status.COMPLETED
        progress.completed_at = timezone.now()
        progress.xp_earned = xp
        progress.save()

    # Count a trial lesson only the first time, for non-premium users.
    if lesson.is_trial and not premium and not was_completed:
        profile.trial_lessons_used += 1
        profile.save(update_fields=['trial_lessons_used', 'updated_at'])

    stats = _award_xp_and_streak(profile, xp, completed_session=not was_completed)
    unlocked = _check_achievements(profile, stats)
    _recompute_weak_skills(profile)

    trial_left = max(0, settings.TRIAL_LESSONS_LIMIT - profile.trial_lessons_used)

    return {
        'xp_earned': xp,
        'total_xp': stats.xp_total,
        'level': stats.level,
        'level_up': getattr(stats, '_level_up', False),
        'streak': stats.current_streak,
        'correct': progress.correct_count if progress else 0,
        'total': progress.total_answered if progress else 0,
        'unlocked': unlocked,
        'is_trial': lesson.is_trial,
        'premium': premium,
        'trial_left': trial_left,
        'need_paywall': not premium,
    }


def _award_xp_and_streak(profile, xp: int, *, completed_session: bool) -> UserStats:
    stats, _ = UserStats.objects.get_or_create(user=profile)
    old_level = stats.level
    stats.xp_total += xp
    stats.level = stats.xp_total // XP_PER_LEVEL + 1
    stats._level_up = stats.level > old_level

    today = timezone.localdate()
    if stats.last_study_date == today:
        pass
    elif stats.last_study_date == today - timedelta(days=1):
        stats.current_streak += 1
    else:
        stats.current_streak = 1
    stats.last_study_date = today
    stats.longest_streak = max(stats.longest_streak, stats.current_streak)

    if completed_session:
        stats.completed_sessions_count += 1

    stats.save()
    return stats


def _recompute_weak_skills(profile) -> None:
    """Update profile.weak_skills from accumulated StepAttempt accuracy per skill."""
    from django.db.models import Count, Q

    from study_app.models import StepAttempt

    rows = (
        StepAttempt.objects.filter(user=profile)
        .values('step__skill')
        .annotate(total=Count('id'), correct=Count('id', filter=Q(is_correct=True)))
    )
    tested = set()
    attempt_weak = set()
    for row in rows:
        skill = row['step__skill']
        total = row['total'] or 0
        if not skill or skill == 'mixed' or total < 2:
            continue
        tested.add(skill)
        if (row['correct'] / total) < 0.5:
            attempt_weak.add(skill)

    # Keep diagnostic weaknesses only for skills we haven't retested enough yet;
    # a retested-and-passed skill drops off the list.
    kept_from_diag = {s for s in (profile.weak_skills or []) if s not in tested}
    profile.weak_skills = sorted(attempt_weak | kept_from_diag)[:6]
    profile.save(update_fields=['weak_skills', 'updated_at'])


def _unlock(profile, code: str, unlocked: list) -> None:
    achievement = Achievement.objects.filter(code=code, is_active=True).first()
    if not achievement:
        return
    obj, created = UserAchievement.objects.get_or_create(
        user=profile, achievement=achievement,
    )
    if created:
        unlocked.append({
            'title': achievement.title,
            'icon': achievement.icon,
            'xp': achievement.xp_reward,
        })
        if achievement.xp_reward:
            stats, _ = UserStats.objects.get_or_create(user=profile)
            stats.xp_total += achievement.xp_reward
            stats.save(update_fields=['xp_total', 'updated_at'])


def _check_achievements(profile, stats: UserStats) -> list:
    unlocked: list = []
    if stats.completed_sessions_count >= 1:
        _unlock(profile, 'first-session', unlocked)
    if stats.current_streak >= 3:
        _unlock(profile, 'three-day-streak', unlocked)

    from study_app.models import StepAttempt

    correct_total = StepAttempt.objects.filter(
        user=profile, is_correct=True,
    ).count()
    if correct_total >= 10:
        _unlock(profile, 'ten-correct-answers', unlocked)
    return unlocked


@sync_to_async
def unlock_achievement(profile_id: int, code: str) -> dict | None:
    profile = UserProfile.objects.get(id=profile_id)
    unlocked: list = []
    _unlock(profile, code, unlocked)
    return unlocked[0] if unlocked else None


# --------------------------------------------------------------------------- #
# Progress / dictionary
# --------------------------------------------------------------------------- #

@sync_to_async
def get_roadmap(profile_id: int) -> dict:
    from study_app.services.roadmap import build_roadmap

    profile = UserProfile.objects.get(id=profile_id)
    return build_roadmap(profile)


@sync_to_async
def get_progress_summary(profile_id: int) -> dict:
    from study_app.models import LessonProgress

    profile = UserProfile.objects.get(id=profile_id)
    stats, _ = UserStats.objects.get_or_create(user=profile)
    completed = LessonProgress.objects.filter(
        user_id=profile.id, status=LessonProgress.Status.COMPLETED,
    ).count()
    sub = Subscription.objects.filter(
        user_id=profile.id, status=Subscription.Status.ACTIVE,
        expires_at__gt=timezone.now(),
    ).order_by('-expires_at').first()

    return {
        'level': (profile.cefr_level or '').upper() or 'не определён',
        'xp': stats.xp_total,
        'user_level': stats.level,
        'streak': stats.current_streak,
        'longest_streak': stats.longest_streak,
        'completed_lessons': completed,
        'trial_used': profile.trial_lessons_used,
        'trial_limit': settings.TRIAL_LESSONS_LIMIT,
        'subscription_until': sub.expires_at.strftime('%d.%m.%Y') if sub else None,
    }


# Spaced-repetition intervals (days) indexed by consecutive correct answers.
SRS_INTERVALS_DAYS = [1, 3, 7, 14, 30, 60]


@sync_to_async
def save_lesson_words(profile_id: int, words: list[dict]) -> int:
    """Add a lesson's vocabulary to the learner's personal dictionary (SRS)."""
    from learning.models import Word
    from progress_app.models import UserWordProgress

    added = 0
    for w in words:
        en = (w.get('en') or '').strip()
        if not en:
            continue
        word, _ = Word.objects.get_or_create(
            english=en,
            defaults={'translation': w.get('ru', ''), 'example': w.get('example', '')},
        )
        # Backfill translation/example if the word was created empty elsewhere.
        changed = False
        if not word.translation and w.get('ru'):
            word.translation = w['ru']
            changed = True
        if not word.example and w.get('example'):
            word.example = w['example']
            changed = True
        if changed:
            word.save(update_fields=['translation', 'example', 'updated_at'])

        _, created = UserWordProgress.objects.get_or_create(
            user_id=profile_id, word=word,
            defaults={'next_review_at': timezone.now()},
        )
        if created:
            added += 1
    return added


@sync_to_async
def get_dictionary_words(profile_id: int, limit: int = 12) -> list[dict]:
    from progress_app.models import UserWordProgress

    qs = (
        UserWordProgress.objects.filter(user_id=profile_id)
        .select_related('word')
        .order_by('next_review_at', '-updated_at')[:limit]
    )
    words = []
    for uwp in qs:
        words.append({
            'english': uwp.word.english,
            'translation': uwp.word.translation,
            'example': uwp.word.example,
            'status': uwp.status,
        })
    return words


@sync_to_async
def get_due_words(profile_id: int, limit: int = 8) -> list[dict]:
    from progress_app.models import UserWordProgress

    now = timezone.now()
    qs = (
        UserWordProgress.objects.filter(user_id=profile_id)
        .filter(Q(next_review_at__lte=now) | Q(next_review_at__isnull=True))
        .select_related('word')
        .order_by('next_review_at')[:limit]
    )
    return [
        {
            'word_id': uwp.word_id,
            'english': uwp.word.english,
            'translation': uwp.word.translation,
            'example': uwp.word.example,
        }
        for uwp in qs
    ]


@sync_to_async
def record_word_review(profile_id: int, word_id: int, correct: bool) -> None:
    from progress_app.models import UserWordProgress

    uwp = UserWordProgress.objects.filter(user_id=profile_id, word_id=word_id).first()
    if not uwp:
        return
    now = timezone.now()
    uwp.last_reviewed_at = now
    if correct:
        uwp.correct_count += 1
        idx = min(uwp.correct_count - 1, len(SRS_INTERVALS_DAYS) - 1)
        uwp.next_review_at = now + timedelta(days=SRS_INTERVALS_DAYS[idx])
        uwp.strength = min(1.0, uwp.strength + 0.2)
        if uwp.correct_count >= 5:
            uwp.status = UserWordProgress.Status.MASTERED
        elif uwp.correct_count >= 3:
            uwp.status = UserWordProgress.Status.KNOWN
        else:
            uwp.status = UserWordProgress.Status.LEARNING
    else:
        uwp.wrong_count += 1
        uwp.next_review_at = now + timedelta(minutes=10)
        uwp.strength = max(0.0, uwp.strength - 0.2)
        uwp.status = UserWordProgress.Status.LEARNING
    uwp.save()


# --------------------------------------------------------------------------- #
# Mentor character media (GIF / photo / video note)
# --------------------------------------------------------------------------- #

@sync_to_async
def get_character_media(character_name: str, key: str) -> dict | None:
    from django.db.utils import OperationalError, ProgrammingError

    from content_app.models import Character, CharacterMedia

    try:
        clip = (
            CharacterMedia.objects.filter(
                character__name__iexact=character_name,
                key=key,
            )
            .select_related('character')
            .first()
        )
    except (OperationalError, ProgrammingError) as exc:
        import logging
        logging.getLogger(__name__).warning(
            'CharacterMedia unavailable (run migrate?): %s', exc,
        )
        return None

    if not clip or not clip.telegram_file_id:
        return None
    return {
        'key': clip.key,
        'kind': clip.kind,
        'file_id': clip.telegram_file_id,
        'note_file_id': clip.telegram_video_note_id,
        'title': clip.title,
    }


@sync_to_async
def get_in_progress_lesson(profile_id: int) -> dict | None:
    """Latest lesson started but not finished (step > 0)."""
    from study_app.models import LessonProgress

    progress = (
        LessonProgress.objects.filter(
            user_id=profile_id,
            status=LessonProgress.Status.IN_PROGRESS,
            current_step_index__gt=0,
        )
        .select_related('lesson')
        .order_by('-started_at')
        .first()
    )
    if not progress:
        return None
    return {
        'lesson_id': progress.lesson_id,
        'title': progress.lesson.title,
        'step_index': progress.current_step_index,
    }


# --------------------------------------------------------------------------- #
# Daily plan
# --------------------------------------------------------------------------- #

@sync_to_async
def get_daily_plan(profile_id: int) -> dict:
    from study_app.services.daily_plan import build_or_get_daily_plan

    profile = UserProfile.objects.get(id=profile_id)
    return build_or_get_daily_plan(profile)


@sync_to_async
def mark_plan_block_done(profile_id: int, block_id: int) -> None:
    from study_app.models import DailySession, DailySessionBlock

    block = DailySessionBlock.objects.select_related('session').get(id=block_id)
    if block.session.user_id != profile_id:
        return
    block.is_completed = True
    block.save(update_fields=['is_completed'])
    session = block.session

    from study_app.services.daily_plan import ensure_bonus_blocks
    ensure_bonus_blocks(session, UserProfile.objects.get(id=profile_id))

    if not session.blocks.filter(is_completed=False).exists():
        session.status = DailySession.Status.COMPLETED
        session.completed_at = timezone.now()
        session.save(update_fields=['status', 'completed_at', 'updated_at'])
    elif session.status == DailySession.Status.PLANNED:
        session.status = DailySession.Status.ACTIVE
        session.started_at = session.started_at or timezone.now()
        session.save(update_fields=['status', 'started_at', 'updated_at'])


# --------------------------------------------------------------------------- #
# Grammar rules library
# --------------------------------------------------------------------------- #

@sync_to_async
def set_user_rule_status(profile_id: int, rule_key: str, status: str) -> dict | None:
    from content_app.models import GrammarRule
    from progress_app.models import UserRule

    rule = GrammarRule.objects.filter(key=rule_key, is_published=True).first()
    if not rule:
        return None
    obj, _ = UserRule.objects.update_or_create(
        user_id=profile_id,
        rule=rule,
        defaults={'status': status},
    )
    return {'rule_id': rule.id, 'key': rule.key, 'title': rule.title, 'status': obj.status}


def _levels_up_to(level: str) -> list[str]:
    if level not in LEVELS:
        level = 'a1'
    return LEVELS[: LEVELS.index(level) + 1]


@sync_to_async
def get_rules_map(profile_id: int) -> dict:
    from content_app.models import GrammarRule
    from progress_app.models import UserRule

    profile = UserProfile.objects.get(id=profile_id)
    level = (profile.cefr_level or 'A1').lower()
    allowed = _levels_up_to(level)

    user_status = {
        ur.rule_id: ur.status
        for ur in UserRule.objects.filter(user_id=profile_id).select_related('rule')
    }

    topics: dict[str, list] = {}
    topic_order: dict[str, int] = {}
    for rule in GrammarRule.objects.filter(is_published=True, level__in=allowed):
        st = user_status.get(rule.id, '')
        if st == 'learned':
            mark = '✅'
        elif st == 'known':
            mark = '🟢'
        else:
            mark = '⬜'
        topics.setdefault(rule.topic, []).append({
            'id': rule.id,
            'key': rule.key,
            'title': rule.title,
            'level': rule.level.upper(),
            'summary_ru': (rule.summary_ru or '')[:120],
            'mark': mark,
            'status': st,
            'order': rule.order,
        })
        topic_order[rule.topic] = min(topic_order.get(rule.topic, 999), rule.order)

    for topic in topics:
        topics[topic].sort(key=lambda r: (r['order'], r['title']))

    sorted_topics = dict(
        sorted(topics.items(), key=lambda kv: (topic_order.get(kv[0], 999), kv[0]))
    )

    return {'topics': sorted_topics, 'level': level.upper(), 'total': sum(len(v) for v in sorted_topics.values())}


@sync_to_async
def get_rule_detail(profile_id: int, rule_key: str) -> dict | None:
    from content_app.models import GrammarRule
    from progress_app.models import UserRule

    rule = GrammarRule.objects.filter(key=rule_key, is_published=True).first()
    if not rule:
        return None
    ur = UserRule.objects.filter(user_id=profile_id, rule=rule).first()
    return {
        'key': rule.key,
        'title': rule.title,
        'topic': rule.topic,
        'level': rule.level,
        'summary_ru': rule.summary_ru,
        'table': rule.table,
        'examples': rule.examples,
        'tip_ru': rule.tip_ru,
        'status': ur.status if ur else '',
    }


@sync_to_async
def get_rule_drill(profile_id: int) -> dict | None:
    """Pick one unpublished rule for sparrow-style MC drill."""
    from content_app.models import GrammarRule
    from progress_app.models import UserRule

    profile = UserProfile.objects.get(id=profile_id)
    level = (profile.cefr_level or 'A1').lower()
    allowed = _levels_up_to(level)
    known_ids = set(
        UserRule.objects.filter(
            user_id=profile_id,
            status__in=[UserRule.Status.LEARNED, UserRule.Status.KNOWN],
        ).values_list('rule_id', flat=True)
    )
    rule = (
        GrammarRule.objects.filter(is_published=True, level__in=allowed)
        .exclude(id__in=known_ids)
        .order_by('order', 'id')
        .first()
    )
    if not rule:
        return None
    examples = rule.examples or []
    if not examples:
        return None
    ex = examples[0]
    if isinstance(ex, dict):
        correct = ex.get('en', '')
        ru = ex.get('ru', '')
    else:
        correct = str(ex)
        ru = ''
    if not correct:
        return None
    # Simple drill: pick the correct EN sentence among distractors from other rules.
    distractors = []
    for other in GrammarRule.objects.filter(is_published=True).exclude(id=rule.id)[:5]:
        for oex in other.examples or []:
            if isinstance(oex, dict) and oex.get('en'):
                distractors.append(oex['en'])
    options = [correct]
    for d in distractors:
        if d not in options and len(options) < 4:
            options.append(d)
    if len(options) < 2:
        return None
    import random
    random.shuffle(options)
    return {
        'rule_key': rule.key,
        'rule_title': rule.title,
        'rule_level': rule.level.upper(),
        'prompt_ru': (
            f'Правило «{rule.title}» ({rule.level.upper()}).\n'
            f'Выбери подходящий пример на английском:'
        ),
        'hint_ru': ru or rule.summary_ru,
        'options': options,
        'correct': [correct],
    }


def _rule_as_dict(rule) -> dict:
    return {
        'key': rule.key,
        'title': rule.title,
        'level': rule.level,
        'topic': rule.topic,
        'summary_ru': rule.summary_ru,
        'table': rule.table,
        'examples': rule.examples,
        'tip_ru': rule.tip_ru,
    }


@sync_to_async
def get_next_unlearned_rule_key(profile_id: int) -> str | None:
    from content_app.models import GrammarRule
    from progress_app.models import UserRule

    profile = UserProfile.objects.get(id=profile_id)
    level = (profile.cefr_level or 'A1').lower()
    allowed = _levels_up_to(level)
    known_ids = set(
        UserRule.objects.filter(
            user_id=profile_id,
            status__in=[UserRule.Status.LEARNED, UserRule.Status.KNOWN],
        ).values_list('rule_id', flat=True)
    )
    rule = (
        GrammarRule.objects.filter(is_published=True, level__in=allowed)
        .exclude(id__in=known_ids)
        .order_by('order', 'id')
        .first()
    )
    return rule.key if rule else None


@sync_to_async
def get_rule_training(rule_key: str) -> dict | None:
    """Exercise set (3–4 steps) for one grammar rule."""
    from content_app.models import GrammarRule
    from content_app.rule_training import build_rule_training_exercises

    try:
        rule = GrammarRule.objects.get(key=rule_key, is_published=True)
    except GrammarRule.DoesNotExist:
        return None
    rule_dict = _rule_as_dict(rule)
    exercises = build_rule_training_exercises(rule_dict)
    if not exercises:
        return None
    return {
        'rule_key': rule.key,
        'rule_title': rule.title,
        'rule_level': rule.level.upper(),
        'exercises': exercises,
    }

# --------------------------------------------------------------------------- #
# Notifications
# --------------------------------------------------------------------------- #

@sync_to_async
def get_notification_settings(profile_id: int) -> dict:
    profile = UserProfile.objects.get(id=profile_id)
    t = profile.reminder_time
    return {
        'enabled': profile.notifications_enabled,
        'time': t.strftime('%H:%M') if t else '',
        'setup_done': profile.reminder_setup_done,
        'timezone': profile.timezone,
    }


@sync_to_async
def set_notifications(profile_id: int, *, enabled: bool, time_str: str = '',
                      setup_done: bool = True) -> None:
    from datetime import datetime

    profile = UserProfile.objects.get(id=profile_id)
    profile.notifications_enabled = enabled
    profile.reminder_setup_done = setup_done
    if time_str:
        profile.reminder_time = datetime.strptime(time_str, '%H:%M').time()
    profile.save(update_fields=[
        'notifications_enabled', 'reminder_time', 'reminder_setup_done', 'updated_at',
    ])


@sync_to_async
def users_due_reminder(hour: int, minute: int = 0) -> list[dict]:
    """Profiles whose reminder_time matches (MVP: Europe/Moscow local hour)."""
    from study_app.services.daily_plan import build_or_get_daily_plan

    qs = UserProfile.objects.filter(
        notifications_enabled=True,
        telegram_id__isnull=False,
        reminder_time__hour=hour,
        reminder_time__minute=minute,
    )
    result = []
    for profile in qs:
        from study_app.services.daily_plan import is_rest_day

        if is_rest_day(profile, timezone.localdate()):
            continue
        plan = build_or_get_daily_plan(profile)
        result.append({
            'telegram_id': profile.telegram_id,
            'first_name': profile.first_name or '',
            'plan': plan,
        })
    return result


def users_due_inactive_nudge(days: int = 7) -> list[dict]:
    """Users inactive N+ days who have not been nudged since last visit."""
    from datetime import timedelta

    from django.db.models import F, Q

    cutoff = timezone.now() - timedelta(days=days)
    qs = UserProfile.objects.filter(
        telegram_id__isnull=False,
        diagnostic_completed=True,
        is_active=True,
        last_seen__isnull=False,
        last_seen__lt=cutoff,
    ).filter(
        Q(last_inactive_nudge_at__isnull=True)
        | Q(last_inactive_nudge_at__lt=F('last_seen')),
    )
    now = timezone.now()
    return [
        {
            'profile_id': p.id,
            'telegram_id': p.telegram_id,
            'first_name': p.first_name or '',
            'days_away': (now - p.last_seen).days,
        }
        for p in qs
    ]


def mark_inactive_nudge_sent(profile_id: int) -> None:
    UserProfile.objects.filter(id=profile_id).update(
        last_inactive_nudge_at=timezone.now(),
    )


# --------------------------------------------------------------------------- #
# Billing
# --------------------------------------------------------------------------- #

def _plan_dict(plan: SubscriptionPlan) -> dict:
    return {
        'id': plan.id,
        'code': plan.code,
        'name': plan.name,
        'price_rub': plan.price_rub,
        'price_kopeks': plan.price_kopeks,
        'duration_days': plan.duration_days,
        'plan_kind': plan.plan_kind,
        'voice_minutes_monthly': plan.voice_minutes_monthly,
        'voice_minutes_in_pack': plan.voice_minutes_in_pack,
        'tutor_ai_daily_limit': plan.tutor_ai_daily_limit,
        'tutor_ai_monthly_limit': plan.tutor_ai_monthly_limit,
        'stt_model': plan.stt_model,
        'description': plan.description,
        'sort_order': plan.sort_order,
    }


@sync_to_async
def get_subscription_plans() -> list[dict]:
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price_rub')
    if not plans.exists():
        from billing_app.plans_catalog import PLANS
        return [
            {
                'id': None,
                'code': p['code'],
                'name': p['name'],
                'price_rub': p['price_rub'],
                'price_kopeks': p['price_rub'] * 100,
                'duration_days': p['duration_days'],
                'plan_kind': p['plan_kind'],
                'voice_minutes_monthly': p['voice_minutes_monthly'],
                'voice_minutes_in_pack': p['voice_minutes_in_pack'],
                'tutor_ai_daily_limit': p['tutor_ai_daily_limit'],
                'tutor_ai_monthly_limit': p['tutor_ai_monthly_limit'],
                'stt_model': p['stt_model'],
                'description': p['description'],
                'sort_order': p['sort_order'],
            }
            for p in PLANS
        ]
    return [_plan_dict(p) for p in plans]


@sync_to_async
def get_plan_by_code(plan_code: str) -> dict | None:
    plan = SubscriptionPlan.objects.filter(code=plan_code, is_active=True).first()
    if plan:
        return _plan_dict(plan)
    from billing_app.plans_catalog import PLANS
    for p in PLANS:
        if p['code'] == plan_code:
            return {
                'id': None,
                'code': p['code'],
                'name': p['name'],
                'price_rub': p['price_rub'],
                'price_kopeks': p['price_rub'] * 100,
                'duration_days': p['duration_days'],
                'plan_kind': p['plan_kind'],
                'voice_minutes_monthly': p['voice_minutes_monthly'],
                'voice_minutes_in_pack': p['voice_minutes_in_pack'],
                'tutor_ai_daily_limit': p['tutor_ai_daily_limit'],
                'tutor_ai_monthly_limit': p['tutor_ai_monthly_limit'],
                'stt_model': p['stt_model'],
                'description': p['description'],
                'sort_order': p['sort_order'],
            }
    return None


@sync_to_async
def get_user_limits(profile_id: int) -> dict:
    from billing_app.limits import get_user_limits as _limits, voice_remaining_minutes

    profile = UserProfile.objects.get(id=profile_id)
    data = _limits(profile)
    data['voice_remaining_minutes'] = voice_remaining_minutes(profile)
    return data


@sync_to_async
def check_voice_usage(profile_id: int, duration_sec: int) -> tuple[bool, str]:
    from billing_app.limits import can_use_voice_seconds

    profile = UserProfile.objects.get(id=profile_id)
    return can_use_voice_seconds(profile, duration_sec)


@sync_to_async
def record_voice_usage(profile_id: int, duration_sec: int) -> None:
    from billing_app.limits import register_voice_usage

    profile = UserProfile.objects.get(id=profile_id)
    register_voice_usage(profile, duration_sec)


@sync_to_async
def check_tutor_message(profile_id: int) -> tuple[bool, str]:
    from billing_app.limits import can_send_tutor_message

    profile = UserProfile.objects.get(id=profile_id)
    return can_send_tutor_message(profile)


@sync_to_async
def register_tutor_message(profile_id: int) -> None:
    from billing_app.limits import register_tutor_message as _register

    profile = UserProfile.objects.get(id=profile_id)
    _register(profile)


@sync_to_async
def get_or_create_plan() -> dict:
    """Legacy helper — returns Basic plan."""
    plan, _ = SubscriptionPlan.objects.get_or_create(
        code='basic',
        defaults={
            'name': 'Basic',
            'price_rub': 590,
            'duration_days': settings.SUBSCRIPTION_DAYS,
            'is_active': True,
        },
    )
    return _plan_dict(plan)


@sync_to_async
def has_active_subscription(profile_id: int) -> bool:
    return _has_active_subscription(profile_id)


@sync_to_async
def activate_mock_subscription(profile_id: int, plan_code: str = 'basic') -> dict:
    from billing_app.limits import add_voice_bonus_minutes

    profile = UserProfile.objects.get(id=profile_id)
    plan = SubscriptionPlan.objects.filter(code=plan_code, is_active=True).first()
    if not plan:
        from billing_app.plans_catalog import PLANS
        spec = next((p for p in PLANS if p['code'] == plan_code), PLANS[0])
        plan, _ = SubscriptionPlan.objects.update_or_create(
            code=spec['code'],
            defaults={
                'name': spec['name'],
                'price_rub': spec['price_rub'],
                'duration_days': spec['duration_days'],
                'plan_kind': spec['plan_kind'],
                'voice_minutes_monthly': spec['voice_minutes_monthly'],
                'voice_minutes_in_pack': spec['voice_minutes_in_pack'],
                'tutor_ai_daily_limit': spec['tutor_ai_daily_limit'],
                'tutor_ai_monthly_limit': spec['tutor_ai_monthly_limit'],
                'stt_model': spec['stt_model'],
                'description': spec['description'],
                'sort_order': spec['sort_order'],
                'is_active': True,
            },
        )

    Payment.objects.create(
        user=profile,
        plan=plan,
        provider='mock',
        status=Payment.Status.SUCCEEDED,
        amount_rub=plan.price_rub,
        currency='RUB',
        payload=f'mock:{profile.id}:{plan.code}',
        raw_data={'mode': 'mock', 'plan_code': plan.code},
    )

    if plan.plan_kind == SubscriptionPlan.PlanKind.VOICE_ADDON:
        if not _has_active_subscription(profile.id):
            return {'ok': False, 'reason': 'no_subscription'}
        add_voice_bonus_minutes(profile, plan.voice_minutes_in_pack)
        from billing_app.limits import voice_remaining_minutes
        return {
            'ok': True,
            'kind': 'voice_addon',
            'minutes_added': plan.voice_minutes_in_pack,
            'voice_remaining_minutes': voice_remaining_minutes(profile),
        }

    sub = Subscription.activate(profile, plan)
    return {
        'ok': True,
        'kind': 'subscription',
        'plan_code': plan.code,
        'plan_name': plan.name,
        'expires_at': sub.expires_at.strftime('%d.%m.%Y'),
    }
