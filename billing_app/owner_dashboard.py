"""Owner-facing user/subscription snapshot (Telegram /owner, alerts)."""

from __future__ import annotations

from django.utils import timezone

from billing_app.models import Payment, Subscription
from billing_app.trial_access import access_tier_label, has_active_subscription, trial_days_remaining
from users_app.models import UserProfile

TIER_RU = {
    'free': 'Free',
    'trial': 'Пробный',
    'paid': 'Платный',
}


def owner_dashboard_text(*, recent_limit: int = 12) -> str:
    qs = UserProfile.objects.filter(telegram_id__isnull=False).order_by('-created_at')
    total = qs.count()
    free = trial = paid = 0
    for p in qs.iterator():
        tier = access_tier_label(p)
        if tier == 'free':
            free += 1
        elif tier == 'trial':
            trial += 1
        elif tier == 'paid':
            paid += 1

    lines = [
        '<b>📊 Пользователи бота</b>',
        '',
        f'Всего: <b>{total}</b> · Free: {free} · Пробный: {trial} · Платный: {paid}',
        '',
        f'<b>Последние {recent_limit} (новые сверху):</b>',
    ]

    recent = list(qs[:recent_limit])
    if not recent:
        lines.append('<i>Пока никого — жди /start в боте.</i>')
    else:
        for p in recent:
            tier = access_tier_label(p)
            name = (p.first_name or p.telegram_username or '—')[:18]
            seen = p.last_seen.strftime('%d.%m %H:%M') if p.last_seen else '—'
            extra = ''
            if tier == 'trial':
                extra = f', {trial_days_remaining(p)} дн trial'
            elif tier == 'paid':
                sub = (
                    Subscription.objects.filter(
                        user_id=p.id,
                        status=Subscription.Status.ACTIVE,
                        expires_at__gt=timezone.now(),
                    )
                    .select_related('plan')
                    .order_by('-expires_at')
                    .first()
                )
                if sub:
                    extra = f', {sub.plan.code} до {sub.expires_at:%d.%m.%Y}'
            paid_flag = '💳' if has_active_subscription(p) else ''
            lines.append(
                f'• {name} · {TIER_RU.get(tier, tier)}{extra} · {seen} {paid_flag}'.rstrip()
            )

    last_pay = (
        Payment.objects.filter(status=Payment.Status.SUCCEEDED)
        .select_related('user', 'plan')
        .order_by('-created_at')
        .first()
    )
    if last_pay:
        uname = last_pay.user.first_name or last_pay.user.telegram_username or '—'
        plan = last_pay.plan.code if last_pay.plan_id else '—'
        lines.extend([
            '',
            '<b>Последняя оплата:</b>',
            f'{uname} · {plan} · {last_pay.amount_rub} ₽ · {last_pay.created_at:%d.%m %H:%M}',
        ])

    lines.extend([
        '',
        '<i>Обновить: /owner · SSH не нужен.</i>',
    ])
    return '\n'.join(lines)


def new_user_alert_text(profile: UserProfile) -> str:
    name = profile.first_name or profile.telegram_username or '—'
    username = f'@{profile.telegram_username}' if profile.telegram_username else '—'
    return (
        '🆕 <b>Новый пользователь</b>\n\n'
        f'{name} ({username})\n'
        f'id: <code>{profile.telegram_id}</code>\n'
        f'тариф: {TIER_RU.get(access_tier_label(profile), "Free")}\n\n'
        '/owner — полный список'
    )


def payment_alert_text(*, user_name: str, plan_code: str, amount_rub: int) -> str:
    return (
        '💳 <b>Оплата</b>\n\n'
        f'{user_name} · {plan_code} · <b>{amount_rub} ₽</b>\n\n'
        '/owner — статистика'
    )
