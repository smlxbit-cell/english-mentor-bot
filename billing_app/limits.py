"""Voice and tutor usage limits per subscription plan."""

from __future__ import annotations

from datetime import date

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from billing_app.models import Subscription, SubscriptionPlan
from billing_app.plans_catalog import DEFAULT_SUBSCRIPTION_CODE, PLANS
from users_app.models import UserProfile


def _plan_defaults(code: str) -> dict:
    for p in PLANS:
        if p['code'] == code:
            return p
    return PLANS[0]


def get_active_plan(profile: UserProfile) -> SubscriptionPlan | None:
    sub = (
        Subscription.objects.filter(
            user=profile,
            status=Subscription.Status.ACTIVE,
            expires_at__gt=timezone.now(),
            plan__plan_kind=SubscriptionPlan.PlanKind.SUBSCRIPTION,
        )
        .select_related('plan')
        .order_by('-expires_at')
        .first()
    )
    return sub.plan if sub else None


def _base_limits(profile: UserProfile) -> dict:
    """Plan limits without usage counters."""
    plan = get_active_plan(profile)
    if plan:
        return {
            'plan_code': plan.code,
            'plan_name': plan.name,
            'voice_minutes_monthly': plan.voice_minutes_monthly,
            'tutor_ai_daily_limit': plan.tutor_ai_daily_limit,
            'tutor_ai_monthly_limit': plan.tutor_ai_monthly_limit,
            'stt_model': plan.stt_model or settings.OPENAI_WHISPER_MODEL,
            'has_subscription': True,
        }
    return {
        'plan_code': 'trial',
        'plan_name': 'Пробный',
        'voice_minutes_monthly': 10,
        'tutor_ai_daily_limit': 40,
        'tutor_ai_monthly_limit': 120,
        'stt_model': settings.OPENAI_WHISPER_MODEL,
        'has_subscription': False,
    }


def get_user_limits(profile: UserProfile) -> dict:
    """Effective limits for profile (subscription or trial defaults)."""
    data = _base_limits(profile)
    data['tutor_messages_remaining'] = tutor_messages_remaining(profile)
    return data


def _reset_tutor_period_if_needed(profile: UserProfile) -> None:
    period = date.today().strftime('%Y-%m')
    if profile.tutor_usage_period != period:
        profile.tutor_usage_period = period
        profile.tutor_messages_used = 0
        profile.save(update_fields=['tutor_usage_period', 'tutor_messages_used', 'updated_at'])


def tutor_messages_allowance(profile: UserProfile) -> int:
    _reset_tutor_period_if_needed(profile)
    return _base_limits(profile)['tutor_ai_monthly_limit']


def tutor_messages_remaining(profile: UserProfile) -> int:
    _reset_tutor_period_if_needed(profile)
    return max(0, tutor_messages_allowance(profile) - profile.tutor_messages_used)


def can_send_tutor_message(profile: UserProfile) -> tuple[bool, str]:
    """Monthly tutor budget + soft daily anti-spam cap."""
    _reset_tutor_period_if_needed(profile)
    remaining = tutor_messages_remaining(profile)
    if remaining <= 0:
        monthly = tutor_messages_allowance(profile)
        return False, (
            'Вопросы наставнику на этот месяц закончились 💬\n'
            f'В тарифе: {monthly} сообщений/мес (не сгорают за день — '
            'считаются за календарный месяц).\n'
            'С 1-го числа снова будет пакет, или оформи тариф с большим лимитом.'
        )

    soft_daily = _base_limits(profile)['tutor_ai_daily_limit']
    if soft_daily > 0:
        day_key = f'tutor:day:{profile.id}:{date.today().isoformat()}'
        day_count = cache.get(day_key, 0)
        if day_count >= soft_daily:
            return False, (
                'Сегодня уже очень много сообщений наставнику 😅\n'
                f'В месяце ещё ~{remaining} — продолжим завтра. '
                '(Это защита от спама, не от учёбы.)'
            )
    return True, ''


def register_tutor_message(profile: UserProfile) -> None:
    _reset_tutor_period_if_needed(profile)
    profile.tutor_messages_used += 1
    profile.save(update_fields=['tutor_messages_used', 'updated_at'])
    soft_daily = _base_limits(profile)['tutor_ai_daily_limit']
    if soft_daily > 0:
        day_key = f'tutor:day:{profile.id}:{date.today().isoformat()}'
        try:
            cache.incr(day_key)
        except ValueError:
            cache.set(day_key, 1, 60 * 60 * 26)
        else:
            cache.touch(day_key, 60 * 60 * 26)


def _reset_voice_period_if_needed(profile: UserProfile) -> None:
    period = date.today().strftime('%Y-%m')
    if profile.voice_usage_period != period:
        profile.voice_usage_period = period
        profile.voice_seconds_used = 0
        profile.save(update_fields=['voice_usage_period', 'voice_seconds_used', 'updated_at'])


def voice_allowance_seconds(profile: UserProfile) -> int:
    _reset_voice_period_if_needed(profile)
    monthly = _base_limits(profile)['voice_minutes_monthly'] * 60
    return monthly + profile.voice_bonus_seconds - profile.voice_seconds_used


def voice_remaining_minutes(profile: UserProfile) -> int:
    return max(0, voice_allowance_seconds(profile) // 60)


def can_use_voice_seconds(profile: UserProfile, duration_sec: int) -> tuple[bool, str]:
    max_dur = settings.VOICE_MAX_DURATION_SECONDS
    if duration_sec > max_dur:
        return False, (
            f'Голосовое слишком длинное (макс. {max_dur // 60} мин).\n'
            'Это симулятор разговора с наставником, не диктофон 🙂'
        )

    hour_key = f'voice:hour:{profile.id}:{timezone.now().strftime("%Y%m%d%H")}'
    hour_count = cache.get(hour_key, 0)
    if hour_count >= settings.VOICE_MAX_PER_HOUR:
        return False, (
            'Слишком много голосовых за час 😅\n'
            'Сделай паузу 10–15 минут или напиши текстом.'
        )

    if voice_allowance_seconds(profile) < max(1, duration_sec):
        mins = _base_limits(profile)['voice_minutes_monthly']
        return False, (
            'Голосовые минуты на этот месяц закончились 🎙️\n'
            f'В твоём тарифе: {mins} мин/мес.\n'
            'Можно докупить +100 мин (290 ₽) — кнопка «⭐️ Подписка».'
        )
    return True, ''


def register_voice_usage(profile: UserProfile, duration_sec: int) -> None:
    _reset_voice_period_if_needed(profile)
    profile.voice_seconds_used += max(0, duration_sec)
    profile.save(update_fields=['voice_seconds_used', 'updated_at'])
    hour_key = f'voice:hour:{profile.id}:{timezone.now().strftime("%Y%m%d%H")}'
    try:
        cache.incr(hour_key)
    except ValueError:
        cache.set(hour_key, 1, 60 * 60 + 60)
    else:
        cache.touch(hour_key, 60 * 60 + 60)


def add_voice_bonus_minutes(profile: UserProfile, minutes: int) -> None:
    profile.voice_bonus_seconds += minutes * 60
    profile.save(update_fields=['voice_bonus_seconds', 'updated_at'])
