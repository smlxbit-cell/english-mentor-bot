"""Telegram keyboards (inline for flow actions, reply for the main menu)."""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

# Reply-menu buttons (persistent bottom keyboard).
BTN_LEARN = '📚 Учиться'
BTN_PROFILE = '👤 Профиль'
BTN_PROGRESS = '📊 Прогресс'
BTN_WORDS = '🗂 Словарь'
BTN_RULES = '📖 Правила'
BTN_TUTOR = '💬 Наставник'
BTN_SUBSCRIBE = '⭐️ Подписка'


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_LEARN],
            [BTN_PROFILE, BTN_PROGRESS],
            [BTN_WORDS, BTN_RULES],
            [BTN_TUTOR, BTN_SUBSCRIBE],
        ],
        resize_keyboard=True,
    )


# --------------------------------------------------------------------------- #
# Navigation helpers
# --------------------------------------------------------------------------- #

def to_menu_kb(label: str = '🏠 В меню') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data='nav:menu')]]
    )


def say_kb(label: str = '🔊 Слушать') -> InlineKeyboardMarkup:
    """Generic 'listen' button that voices context.user_data['tts_text']."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data='tts:say')]]
    )


# --------------------------------------------------------------------------- #
# Diagnostic
# --------------------------------------------------------------------------- #

def start_diagnostic_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton('🎯 Пройти диагностику', callback_data='diag:start')]]
    )


def diagnostic_options_kb(options: list[str], with_listen: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
    rows += [
        [InlineKeyboardButton(opt, callback_data=f'diag:opt:{i}')]
        for i, opt in enumerate(options)
    ]
    return InlineKeyboardMarkup(rows)


# --------------------------------------------------------------------------- #
# Lesson flow
# --------------------------------------------------------------------------- #

def continue_kb(label: str = '➡️ Далее') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data='lesson:next')]]
    )


def continue_with_listen_kb(label: str = '➡️ Далее') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🔊 Слушать', callback_data='tts:step')],
            [InlineKeyboardButton(label, callback_data='lesson:next')],
        ]
    )


def listen_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton('🔊 Слушать образец', callback_data='tts:step')]]
    )


def dict_listen_kb(has_words: bool = True) -> InlineKeyboardMarkup:
    rows = []
    if has_words:
        rows.append([InlineKeyboardButton('🔊 Слушать слова', callback_data='tts:dict')])
        rows.append([InlineKeyboardButton('🎓 Тренировать слова', callback_data='srs:start')])
    rows.append([InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')])
    return InlineKeyboardMarkup(rows)


def srs_next_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')],
            [InlineKeyboardButton('➡️ Следующее слово', callback_data='srs:next')],
            [InlineKeyboardButton('🏁 Закончить', callback_data='nav:menu')],
        ]
    )


def exercise_options_kb(
    options: list[str],
    *,
    with_listen: bool = False,
    with_ask: bool = False,
    with_hint: bool = False,
) -> InlineKeyboardMarkup:
    rows = []
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
    if with_hint:
        rows.append([InlineKeyboardButton('💡 Подсказка', callback_data='ex:hint')])
    if with_ask:
        rows.append([InlineKeyboardButton('💬 Спросить', callback_data='lesson:ask')])
    rows += [
        [InlineKeyboardButton(opt, callback_data=f'ex:opt:{i}')]
        for i, opt in enumerate(options)
    ]
    return InlineKeyboardMarkup(rows)


def exercise_text_kb(*, with_hint: bool = False, with_ask: bool = True) -> InlineKeyboardMarkup:
    rows = []
    if with_hint:
        rows.append([InlineKeyboardButton('💡 Подсказка', callback_data='ex:hint')])
    if with_ask:
        rows.append([InlineKeyboardButton('💬 Спросить', callback_data='lesson:ask')])
    return InlineKeyboardMarkup(rows) if rows else None


def lessons_list_kb(lessons: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for lesson in lessons:
        mark = '✅ ' if lesson['completed'] else ''
        star = '' if lesson['is_trial'] else '⭐️ '
        rec = '🎯 ' if lesson.get('recommended') else ''
        rows.append([
            InlineKeyboardButton(
                f'{mark}{star}{rec}{lesson["title"]}',
                callback_data=f'lesson:open:{lesson["id"]}',
            )
        ])
    rows.append([InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')])
    return InlineKeyboardMarkup(rows)


def daily_plan_kb(plan: dict) -> InlineKeyboardMarkup:
    """Adventure chapter: one main CTA + optional bonus."""
    rows = []
    if not plan.get('all_done'):
        label = plan.get('continue_label', 'Продолжить')
        rows.append([InlineKeyboardButton(f'▶️ {label[:55]}', callback_data='plan:continue')])

    warmup = plan.get('warmup')
    if warmup and not warmup.get('done'):
        from study_app.daily_facts import warmup_label
        icon, label = warmup_label(warmup.get('kind', 'fact'))
        rows.append([InlineKeyboardButton(f'{icon} {label}', callback_data='plan:warmup')])

    episode = plan.get('episode')
    if episode and not episode.get('done'):
        rows.append([
            InlineKeyboardButton(
                f'📺 {episode.get("title", "Эпизод")[:40]}',
                callback_data=f'plan:episode:{episode["lesson_id"]}',
            )
        ])

    bonus = plan.get('bonus_words')
    if bonus and not bonus.get('done'):
        # Avoid duplicate when main CTA already opens the word bonus.
        if 'Бонус' not in plan.get('continue_label', ''):
            rows.append([
                InlineKeyboardButton(
                    f'🗂 Бонус: слова ({bonus.get("count", 0)})',
                    callback_data='plan:words',
                )
            ])

    rows.append([InlineKeyboardButton('📖 Карта правил', callback_data='rules:map')])
    rows.append([InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')])
    return InlineKeyboardMarkup(rows)


def warmup_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🔊 Слушать по-английски', callback_data='plan:warmup:listen')],
            [InlineKeyboardButton('▶️ К эпизоду', callback_data='plan:warmup:next')],
            [InlineKeyboardButton('↩️ К главе дня', callback_data='plan:back')],
        ]
    )


def grammar_rule_kb(rule_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🔊 Слушать примеры', callback_data='tts:step')],
            [
                InlineKeyboardButton('✅ Выучил', callback_data=f'rule:learn:{rule_key}'),
                InlineKeyboardButton('👌 Уже знаю', callback_data=f'rule:known:{rule_key}'),
            ],
            [InlineKeyboardButton('💬 Спросить', callback_data='lesson:ask')],
            [InlineKeyboardButton('➡️ Далее', callback_data='lesson:next')],
        ]
    )


def lesson_help_kb(label: str = '➡️ Далее') -> InlineKeyboardMarkup:
    """Content step with optional tutor question."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🔊 Слушать', callback_data='tts:step')],
            [InlineKeyboardButton('💬 Спросить', callback_data='lesson:ask')],
            [InlineKeyboardButton(label, callback_data='lesson:next')],
        ]
    )


def rules_topics_kb(topics: dict[str, list]) -> InlineKeyboardMarkup:
    """First level: pick a topic section."""
    rows = []
    for i, (topic, rules) in enumerate(topics.items()):
        done = sum(1 for r in rules if r.get('mark') != '⬜')
        rows.append([
            InlineKeyboardButton(
                f'📂 {topic} ({done}/{len(rules)})',
                callback_data=f'rules:topic:{i}',
            )
        ])
    rows.append([InlineKeyboardButton('🎯 Тренировать правила', callback_data='rules:drill')])
    rows.append([InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')])
    return InlineKeyboardMarkup(rows)


def rules_topic_kb(topic: str, rules: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for rule in rules:
        level = rule.get('level', '')
        label = f'{rule["mark"]} [{level}] {rule["title"]}' if level else f'{rule["mark"]} {rule["title"]}'
        rows.append([
            InlineKeyboardButton(label[:60], callback_data=f'rules:view:{rule["key"]}'),
        ])
    rows.append([InlineKeyboardButton('◀️ К разделам', callback_data='rules:map')])
    rows.append([InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')])
    return InlineKeyboardMarkup(rows)


def rules_map_kb(topics: dict[str, list]) -> InlineKeyboardMarkup:
    return rules_topics_kb(topics)


def rule_detail_kb(rule_key: str, status: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton('🔊 Слушать примеры', callback_data=f'rules:listen:{rule_key}')],
        [
            InlineKeyboardButton('✅ Выучил', callback_data=f'rule:learn:{rule_key}'),
            InlineKeyboardButton('👌 Уже знаю', callback_data=f'rule:known:{rule_key}'),
        ],
        [InlineKeyboardButton('◀️ К карте правил', callback_data='rules:map')],
    ]
    return InlineKeyboardMarkup(rows)


def notification_ask_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🔔 Да, напоминать', callback_data='notify:yes')],
            [InlineKeyboardButton('Не сейчас', callback_data='notify:no')],
        ]
    )


def reminder_time_kb() -> InlineKeyboardMarkup:
    times = ['08:00', '09:00', '12:00', '18:00', '19:00', '20:00', '21:00']
    rows = []
    row: list[InlineKeyboardButton] = []
    for t in times:
        row.append(InlineKeyboardButton(t, callback_data=f'notify:time:{t}'))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')])
    return InlineKeyboardMarkup(rows)


# --------------------------------------------------------------------------- #
# AI dialogue
# --------------------------------------------------------------------------- #

def finish_dialogue_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')],
            [InlineKeyboardButton('✅ Завершить диалог', callback_data='dialogue:finish')],
        ]
    )


# --------------------------------------------------------------------------- #
# Profile / onboarding
# --------------------------------------------------------------------------- #

def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🎯 Мои интересы', callback_data='profile:interests')],
            [InlineKeyboardButton('🎓 Цель обучения', callback_data='profile:goal')],
            [InlineKeyboardButton('💼 Моя сфера', callback_data='profile:sphere')],
            [InlineKeyboardButton('🔔 Напоминания', callback_data='profile:notify')],
            [InlineKeyboardButton('🔁 Пройти диагностику заново', callback_data='profile:rediag')],
        ]
    )


def interests_kb(items: list[dict], selected: set[int]) -> InlineKeyboardMarkup:
    """items: [{'id','name'}]; selected: ids currently chosen."""
    rows = []
    row: list[InlineKeyboardButton] = []
    for it in items:
        mark = '✅ ' if it['id'] in selected else ''
        row.append(InlineKeyboardButton(
            f'{mark}{it["name"]}', callback_data=f'intr:toggle:{it["id"]}',
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton('✅ Готово', callback_data='intr:done')])
    return InlineKeyboardMarkup(rows)


def sphere_kb(spheres: list[dict], selected: str = '') -> InlineKeyboardMarkup:
    """spheres: [{'code','label'}]."""
    rows = []
    row: list[InlineKeyboardButton] = []
    for s in spheres:
        mark = '✅ ' if s['code'] == selected else ''
        row.append(InlineKeyboardButton(
            f'{mark}{s["label"]}', callback_data=f'sph:set:{s["code"]}',
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def goal_kb(goals: list[dict], selected: str = '') -> InlineKeyboardMarkup:
    """goals: [{'code','label'}]."""
    rows = []
    row: list[InlineKeyboardButton] = []
    for g in goals:
        mark = '✅ ' if g['code'] == selected else ''
        row.append(InlineKeyboardButton(
            f'{mark}{g["label"]}', callback_data=f'goal:set:{g["code"]}',
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


# --------------------------------------------------------------------------- #
# Paywall
# --------------------------------------------------------------------------- #

def practice_offer_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🎯 Ещё практика (слабые темы)',
                                  callback_data='practice:weak')],
            [InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')],
        ]
    )


def practice_options_kb(options: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(opt, callback_data=f'pr:opt:{i}')]
        for i, opt in enumerate(options)
    ]
    return InlineKeyboardMarkup(rows)


def practice_again_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🎯 Ещё практика', callback_data='practice:weak')],
            [InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')],
        ]
    )


def paywall_kb(price_rub: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f'Оформить за {price_rub} ₽', callback_data='buy')],
            [InlineKeyboardButton('ℹ️ Условия', callback_data='terms')],
        ]
    )
