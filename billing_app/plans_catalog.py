"""Canonical subscription plans — source of truth for seed_subscription_plans."""

from __future__ import annotations

# Shared marketing copy for paywall / subscription screens.
TARIFF_INCLUDES = (
    '<b>В каждом тарифе — полная программа:</b>\n'
    '• ежедневный план под твой уровень, <b>цели и интересы</b>\n'
    '• история с Emma, уроки и диалоги\n'
    '• словарь с повторением и тренировка слов\n'
    '• карта правил, тренировка грамматики\n'
    '• 💬 наставник на продвинутом AI — текст и голос (RU+EN)\n'
    '  забыл слово — скажи по-русски; поправит ошибки, покажет правила\n\n'
    '<i>Тарифы отличаются в основном голосовыми минутами наставника. '
    'Вопросы наставнику текстом — <b>пакет на месяц</b>, не сгорают за день: '
    'можно пропустить неделю и вернуться с запасом.</i>'
)

TARIFF_INCLUDES_PLAIN = (
    'В каждом тарифе: план дня под цели и интересы, история с Emma, '
    'словарь, тренировка слов и правил, наставник AI (текст + голос). '
    'Тарифы отличаются в основном минутами голоса.'
)

PLANS: tuple[dict, ...] = (
    {
        'code': 'basic',
        'name': 'Basic',
        'price_rub': 590,
        'duration_days': 30,
        'plan_kind': 'subscription',
        'voice_minutes_monthly': 60,
        'voice_minutes_in_pack': 0,
        'tutor_ai_daily_limit': 80,
        'tutor_ai_monthly_limit': 500,
        'stt_model': 'whisper-large-v3-turbo',
        'description': (
            'Полная программа + ~60 мин голоса наставника в месяц. '
            'Для спокойного темпа (~2 мин голоса в день).'
        ),
        'sort_order': 1,
    },
    {
        'code': 'active',
        'name': 'Active',
        'price_rub': 990,
        'duration_days': 30,
        'plan_kind': 'subscription',
        'voice_minutes_monthly': 180,
        'voice_minutes_in_pack': 0,
        'tutor_ai_daily_limit': 120,
        'tutor_ai_monthly_limit': 900,
        'stt_model': 'whisper-large-v3-turbo',
        'description': (
            'Полная программа + ~180 мин голоса наставника в месяц (~6 мин/день). '
            'Для регулярных тренировок 4–5 раз в неделю.'
        ),
        'sort_order': 2,
    },
    {
        'code': 'pro',
        'name': 'Pro',
        'price_rub': 1990,
        'duration_days': 30,
        'plan_kind': 'subscription',
        'voice_minutes_monthly': 450,
        'voice_minutes_in_pack': 0,
        'tutor_ai_daily_limit': 150,
        'tutor_ai_monthly_limit': 1500,
        'stt_model': 'whisper-large-v3-turbo',
        'description': (
            'Полная программа + ~450 мин голоса наставника. '
            'Для интенсивной практики вместо репетитора.'
        ),
        'sort_order': 3,
    },
    {
        'code': 'voice_100',
        'name': '+100 мин голоса',
        'price_rub': 290,
        'duration_days': 0,
        'plan_kind': 'voice_addon',
        'voice_minutes_monthly': 0,
        'voice_minutes_in_pack': 100,
        'tutor_ai_daily_limit': 0,
        'tutor_ai_monthly_limit': 0,
        'stt_model': '',
        'description': 'Докупка 100 минут голосового наставника. Нужна активная подписка.',
        'sort_order': 10,
    },
)

DEFAULT_SUBSCRIPTION_CODE = 'basic'


def format_subscription_plans_message(
    *,
    header: str,
    sub_plans: list[dict],
    days: int,
) -> str:
    """HTML text for paywall / subscription picker."""
    lines = [header, f'Подписка на {days} дней, без автопродления:\n']
    for plan in sub_plans:
        mins = plan.get('voice_minutes_monthly', 0)
        stt_note = ''
        if plan.get('code') == 'pro':
            stt_note = ' · больше минут голоса'
        lines.append(
            f'• <b>{plan["name"]}</b> — {plan["price_rub"]} ₽\n'
            f'  🎙️ {mins} мин голоса наставника/мес{stt_note}'
        )
    lines.append('\n' + TARIFF_INCLUDES)
    return '\n'.join(lines)
