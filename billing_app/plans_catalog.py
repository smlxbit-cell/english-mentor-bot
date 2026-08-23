"""Canonical subscription plans — source of truth for seed_subscription_plans."""

from __future__ import annotations

# --- v3 prices (2026-08-23) ---
BASIC_PRICE_RUB = 349
PRO_PRICE_RUB = 990
VOICE_ADDON_PRICE_RUB = 350
VOICE_ADDON_MINUTES = 100

# Keep in sync with config/settings.py → TRIAL_DAYS
TRIAL_DAYS_LABEL = '3 дня'

RETIRED_PLAN_CODES = frozenset({'active'})

UPGRADE_PATHS: dict[tuple[str, str], int] = {
    ('basic', 'pro'): PRO_PRICE_RUB - BASIC_PRICE_RUB,  # 641 ₽
}


def subscription_plans() -> tuple[dict, ...]:
    """Active subscription tiers only (not voice add-on)."""
    return tuple(p for p in PLANS if p.get('plan_kind') == 'subscription')


def upgrade_price_rub(from_code: str, to_code: str) -> int | None:
    return UPGRADE_PATHS.get((from_code.lower(), to_code.lower()))


def can_upgrade(from_code: str, to_code: str) -> bool:
    return upgrade_price_rub(from_code, to_code) is not None


# Shared marketing copy for paywall / subscription screens.
TARIFF_INCLUDES = (
    '<b>В подписке:</b>\n'
    '• ▶️ <b>План дня</b> — слова, правило, текст на слух, диалог\n'
    '• 📖 <b>Все правила</b> + тренировки\n'
    '• 📚 <b>Слова</b> — как на free, плюс 🎙 говорить в тренировке\n'
    '• 💬 <b>Наставник</b> — текст и голос (RU+EN)\n\n'
    '<i>Тарифы отличаются <b>минутами 🎙</b> (сколько говоришь боту в месяц). '
    '🔊 «Слушать» — без лимита на всех тарифах.</i>'
)

TARIFF_INCLUDES_PLAIN = (
    'Подписка: план дня, все правила, наставник текст+голос. '
    'Basic и Pro отличаются минутами голоса.'
)

FREE_TIER_BLOCK = (
    '<b>🆓 Free — 0 ₽ навсегда</b>\n'
    '• 📚 <b>Слова</b> — весь банк, тренировка, 🔊 слушать\n'
    '• 📖 <b>Грамматика</b> — ознакомительный доступ (часть правил)\n'
    '• 🧪 Диагностика уровня\n'
    '• 💬 Наставник — <b>только текст</b> (20 сообщ./мес)\n'
    '• 🚫 без 🎙 голоса · без ▶️ плана дня\n\n'
    f'<b>🎁 Пробный период {TRIAL_DAYS_LABEL}</b> — вся программа как Basic '
    '(план дня, все правила, голос).\n\n'
)

FREE_TIER_PLAIN = (
    'Free: слова бесплатно, грамматика — ограниченный доступ, наставник текстом. '
    f'Пробный период {TRIAL_DAYS_LABEL} — полная программа.'
)

PLANS: tuple[dict, ...] = (
    {
        'code': 'basic',
        'name': 'Basic',
        'price_rub': BASIC_PRICE_RUB,
        'duration_days': 30,
        'plan_kind': 'subscription',
        'voice_minutes_monthly': 60,
        'voice_minutes_in_pack': 0,
        'tutor_ai_daily_limit': 80,
        'tutor_ai_monthly_limit': 500,
        'stt_model': 'whisper-large-v3-turbo',
        'description': (
            '▶️ План дня + все правила + наставник.\n'
            '🎙 <b>60 мин/мес</b> — ~2 мин говоришь каждый день.'
        ),
        'sort_order': 1,
    },
    {
        'code': 'pro',
        'name': 'Pro',
        'price_rub': PRO_PRICE_RUB,
        'duration_days': 30,
        'plan_kind': 'subscription',
        'voice_minutes_monthly': 240,
        'voice_minutes_in_pack': 0,
        'tutor_ai_daily_limit': 120,
        'tutor_ai_monthly_limit': 1200,
        'stt_model': 'whisper-large-v3-turbo',
        'description': (
            'Всё из Basic.\n'
            '🎙 <b>240 мин/мес</b> — ~8 мин говоришь каждый день.'
        ),
        'sort_order': 2,
    },
    {
        'code': 'voice_100',
        'name': '+100 мин разговора',
        'price_rub': VOICE_ADDON_PRICE_RUB,
        'duration_days': 0,
        'plan_kind': 'voice_addon',
        'voice_minutes_monthly': 0,
        'voice_minutes_in_pack': VOICE_ADDON_MINUTES,
        'tutor_ai_daily_limit': 0,
        'tutor_ai_monthly_limit': 0,
        'stt_model': '',
        'description': (
            f'Дополнительные <b>{VOICE_ADDON_MINUTES} мин</b> 🎙 разговора с ботом '
            'к текущему месяцу. Нужна активная подписка Basic или Pro.'
        ),
        'sort_order': 10,
    },
)

DEFAULT_SUBSCRIPTION_CODE = 'basic'

PLAN_NAMES_RU = {
    'basic': 'Basic',
    'pro': 'Pro',
    'voice_100': '+100 мин разговора',
    'active': 'Active (архив)',
}

PLAN_BUTTON_LABELS = {
    'free': '🆓 Free · слова навсегда',
    'basic': f'Basic {BASIC_PRICE_RUB}₽ · 60 мин 🎙',
    'pro': f'Pro {PRO_PRICE_RUB}₽ · 240 мин 🎙',
    'upgrade_pro': f'↑ Pro +{UPGRADE_PATHS[("basic", "pro")]}₽',
    'voice_100': f'+{VOICE_ADDON_MINUTES} мин 🎙 · {VOICE_ADDON_PRICE_RUB}₽',
}

TARIFF_UTP_BLOCK = (
    '<b>English Mentor</b> — тренажёр + AI-наставник\n'
    '📚 <b>Слова бесплатно</b> · прогресс A1–C1 · 🔊 слушать\n'
    '▶️ <b>Подписка</b> — план дня, все правила, 🎙 говорить с ботом'
)


def plan_button_label(plan: dict) -> str:
    code = plan.get('code', '')
    if code in PLAN_BUTTON_LABELS:
        return PLAN_BUTTON_LABELS[code]
    ru = PLAN_NAMES_RU.get(code, plan.get('name', code))
    price = plan.get('price_rub', 0)
    mins = plan.get('voice_minutes_monthly', 0)
    if mins:
        return f'{ru} {price}₽ · {mins} мин 🎙'
    return f'{ru} {price}₽'


def format_subscription_compact(
    sub_plans: list[dict],
    *,
    access_tier: str = 'free',
    current_plan_code: str = '',
) -> str:
    """Тарифы — понятно с первого взгляда."""
    tier_note = {
        'free': 'Сейчас: <b>Free</b> — слова бесплатно, грамматика — частично',
        'trial': f'Сейчас: <b>Пробный период</b> — полная программа ({TRIAL_DAYS_LABEL})',
        'paid': 'Сейчас: платная подписка',
    }.get(access_tier, '')
    upgrade_line = ''
    if current_plan_code == 'basic':
        diff = upgrade_price_rub('basic', 'pro')
        upgrade_line = (
            f'\n<i>У тебя Basic → Pro за <b>+{diff} ₽</b> '
            f'(не {PRO_PRICE_RUB} ₽ заново)</i>\n'
        )
    blocks = [
        '<b>💳 Тарифы</b>',
        f'<i>{tier_note}</i>' if tier_note else '',
        upgrade_line,
        '',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        f'🆓 <b>FREE · 0 ₽</b>',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        '✅ Слова — весь банк, 🔊 слушать, повтор',
        '✅ Грамматика — ознакомительный доступ',
        '✅ Наставник текст (20 сообщ./мес)',
        '❌ План дня · 🎙 говорить',
        '',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        f'💵 <b>BASIC · {BASIC_PRICE_RUB} ₽ / 30 дней</b>',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        '✅ ▶️ <b>План дня</b> каждый день',
        '✅ <b>Все правила</b> + тренировки',
        '✅ Наставник текст + 🎙 голос',
        f'🎙 <b>60 мин/мес</b> (~2 мин/день) · 500 сообщ.',
        '',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        f'💵 <b>PRO · {PRO_PRICE_RUB} ₽ / 30 дней</b>',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        '✅ Всё из Basic',
        f'🎙 <b>240 мин/мес</b> (~8 мин/день) · 1200 сообщ.',
        '',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        f'⬆️ <b>С Basic на Pro</b> — доплата <b>+{upgrade_price_rub("basic", "pro")} ₽</b>',
        f'<i>(не нужно платить {PRO_PRICE_RUB} ₽ заново)</i>',
        '',
        f'➕ <b>Доп. минуты разговора</b> — +{VOICE_ADDON_MINUTES} мин 🎙 · {VOICE_ADDON_PRICE_RUB} ₽',
        '<i>Если минут не хватает — дополнительные минуты (нужен Basic или Pro). '
        'Выгоднее Pro, если говоришь каждый день.</i>',
        '',
        '👇 Выбери тариф',
    ]
    return '\n'.join(line for line in blocks if line)


def format_subscriber_status(
    *,
    plan_code: str,
    plan_name_ru: str,
    expires_at: str,
    voice_remaining: int,
    voice_monthly: int,
    tutor_remaining: int,
) -> str:
    """Экран «⭐️ Подписка» для активного тарифа."""
    lines = [
        f'✅ <b>{plan_name_ru}</b> · до {expires_at}',
        '',
        f'🎙 Голос: <b>{voice_remaining}</b> из {voice_monthly} мин/мес',
        f'💬 Наставник: <b>{tutor_remaining}</b> сообщ./мес',
        '',
        '🔊 «Слушать» в словах и уроках — без лимита.',
    ]
    if plan_code == 'basic':
        diff = upgrade_price_rub('basic', 'pro')
        lines.extend([
            '',
            '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
            f'⬆️ <b>Нужно больше говорить?</b>',
            f'Pro — <b>+{diff} ₽</b> доплата (ещё +180 мин/мес)',
            f'или +{VOICE_ADDON_MINUTES} доп. мин за {VOICE_ADDON_PRICE_RUB} ₽',
        ])
    elif voice_remaining <= 15:
        lines.extend([
            '',
            f'Минут мало — можно добавить +{VOICE_ADDON_MINUTES} мин разговора '
            f'({VOICE_ADDON_PRICE_RUB} ₽) или перейти на Pro.',
        ])
    return '\n'.join(lines)


def format_subscription_plans_message(
    *,
    header: str,
    sub_plans: list[dict],
    days: int,
    show_free: bool = True,
    free_active: bool = False,
) -> str:
    """HTML text for paywall / subscription picker."""
    lines = [header]
    if show_free:
        prefix = '✅ ' if free_active else ''
        lines.append(prefix + FREE_TIER_BLOCK.strip())
    lines.append(f'<b>Подписки</b> — {days} дней (<i>без автосписания</i>):\n')
    for plan in sub_plans:
        mins = plan.get('voice_minutes_monthly', 0)
        lines.append(
            f'• <b>{plan["name"]}</b> — {plan["price_rub"]} ₽ · 🎙 {mins} мин/мес'
        )
    diff = upgrade_price_rub('basic', 'pro')
    if diff:
        lines.append(f'\n⬆️ С Basic на Pro: доплата <b>+{diff} ₽</b>')
    lines.append('\n' + TARIFF_INCLUDES)
    return '\n'.join(lines)
