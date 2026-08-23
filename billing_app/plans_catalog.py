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
    '<i>Тарифы отличаются лимитом <b>минут голосового диалога</b> с наставником 🎙 '
    '(говоришь боту — он отвечает голосом). '
    'Кнопка 🔊 «Слушать» в уроках — на всех тарифах, без лимита.</i>'
)

TARIFF_INCLUDES_PLAIN = (
    'В каждом тарифе: план дня под цели и интересы, история с Emma, '
    'словарь, тренировка слов и правил, наставник AI (текст + голос). '
    'Тарифы отличаются в основном минутами голоса.'
)

FREE_TIER_BLOCK = (
    '<b>🆓 Free — 0 ₽ навсегда</b>\n'
    '• эпизоды 1–3 сериала, словарь, карта правил\n'
    '• тесты и тренировки <b>текстом</b>\n'
    '• 🔊 озвучка всего английского в уроках\n'
    '• наставник — текст (лимит в месяц)\n'
    '• <i>без голосового ввода 🎙️ (экономим ваши минуты STT)</i>\n\n'
    '<b>+ 2 дня пробного периода</b> — всё открыто, включая голос.\n\n'
)

FREE_TIER_PLAIN = (
    'Free 0 ₽: эпизоды 1–3, словарь, правила, озвучка, наставник текстом. '
    'Без голосового ввода. 2 дня полного trial.'
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
            'Вся программа + ~60 мин <b>голосового диалога</b> 🎙 с наставником в месяц. '
            'Спокойный темп (~2 мин разговора в день).'
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
            'Вся программа + ~180 мин <b>голосового диалога</b> 🎙 (~6 мин/день). '
            '4–5 разговоров с наставником в неделю.'
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
            'Вся программа + ~450 мин <b>голосового диалога</b> 🎙. '
            'Интенсивная практика вместо репетитора.'
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
        'description': 'Докупка 100 минут голосового диалога 🎙. Нужна активная подписка.',
        'sort_order': 10,
    },
)

DEFAULT_SUBSCRIPTION_CODE = 'basic'

PLAN_NAMES_RU = {
    'basic': 'Базовый',
    'active': 'Активный',
    'pro': 'Про',
    'voice_100': '+100 мин голоса',
}

# Короткие подписи для кнопок (лимит Telegram ~64 символа).
PLAN_BUTTON_LABELS = {
    'free': '🆓 0₽ · 3 эпизода · 🔊 слушать · текст',
    'basic': '💵 590₽ · всё + 60 мин 🎙 разговора',
    'active': '💵 990₽ · всё + 180 мин 🎙 разговора',
    'pro': '💵 1990₽ · всё + 450 мин 🎙 разговора',
    'voice_100': '➕ 290₽ · +100 мин разговора 🎙',
}

TARIFF_UTP_BLOCK = (
    '<b>Что умеет бот</b>\n'
    '📖 Программа под ваш уровень — история Emma, уроки, упражнения\n'
    '🔊 <b>Слушайте любой английский</b> — кнопка 🔊 везде (и на бесплатном!)\n'
    '💬 <b>Умный наставник AI</b> — диалог, перевод, разбор ошибок\n'
    '🎙 На платных — <b>говорите голосом</b> (RU+EN), он отвечает голосом'
)


def plan_button_label(plan: dict) -> str:
    code = plan.get('code', '')
    if code in PLAN_BUTTON_LABELS:
        return PLAN_BUTTON_LABELS[code]
    ru = PLAN_NAMES_RU.get(code, plan.get('name', code))
    price = plan.get('price_rub', 0)
    mins = plan.get('voice_minutes_monthly', 0)
    if mins:
        return f'💵 {price}₽ {ru} · {mins} мин 🎙'
    return f'💵 {price}₽ {ru}'


def format_subscription_compact(
    sub_plans: list[dict],
    *,
    access_tier: str = 'free',
) -> str:
    """Тарифы блоками — понятно новому человеку."""
    tier_note = {
        'free': 'Сейчас у вас: бесплатный доступ',
        'trial': 'Сейчас: пробный период — всё открыто',
        'paid': 'Сейчас: платная подписка активна',
    }.get(access_tier, '')
    blocks = [
        '<b>💳 Тарифы</b>',
        f'<i>{tier_note}</i>' if tier_note else '',
        '',
        TARIFF_UTP_BLOCK,
        '',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        '🆓 <b>БЕСПЛАТНО</b> · 0 ₽',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        '📺 Эпизоды 1–3 сериала',
        '📖 Словарь и карта грамматики',
        '🔊 <b>Озвучка всего английского</b> — нажми 🔊 где угодно',
        '💬 Наставник AI — <b>текстом</b>, объясняет и переводит',
        '🚫 Голосом боту говорить нельзя (нет 🎙)',
        '',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        '💰 <b>ПЛАТНЫЕ ТАРИФЫ</b>',
        '<i>Доступ на 30 дней · без автосписания</i>',
        '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬',
        'В каждом платном — <b>всё из бесплатного, плюс:</b>',
        '✅ <b>Все эпизоды</b> — вся история и программа',
        '✅ Наставник AI — диалог, объяснения <b>с переводом</b>, правки',
        '✅ <b>Голос 🎙</b> — говорите боту, он отвечает голосом',
        '✅ Словарь, правила, тренировки — без ограничений по контенту',
        '',
        'Тарифы отличаются <b>лимитом минут голосового диалога</b> 🎙 с наставником:',
        '',
        '💵 <b>590 ₽ · Базовый</b>',
        '🎙 ~60 мин — ~2 мин/день или короткий диалог через день',
        '',
        '💵 <b>990 ₽ · Активный</b>',
        '🎙 ~180 мин — ~6 мин/день, хватит на 4–5 разговоров в неделю',
        '',
        '💵 <b>1990 ₽ · Про</b>',
        '🎙 ~450 мин — ~15 мин/день, много живой практики',
        '',
        '➕ <b>290 ₽ · ещё 100 мин разговора</b>',
        '<i>Если минуты на тарифе закончились — можно добавить 100 мин.\n'
        'Нужен активный платный тариф (Базовый, Активный или Про).</i>',
        '',
        '👇 Выберите тариф кнопкой ниже',
    ]
    return '\n'.join(line for line in blocks if line)


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
    lines.append(f'<b>Платные тарифы</b> — доступ на {days} дней (<i>без автосписания</i>):\n')
    for plan in sub_plans:
        mins = plan.get('voice_minutes_monthly', 0)
        stt_note = ''
        if plan.get('code') == 'pro':
            stt_note = ' · больше минут голоса'
        lines.append(
            f'• <b>{plan["name"]}</b> — {plan["price_rub"]} ₽\n'
            f'  🎙 {mins} мин голосового диалога/мес{stt_note}'
        )
    lines.append('\n' + TARIFF_INCLUDES)
    return '\n'.join(lines)
