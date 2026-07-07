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


def diagnostic_self_assess_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('A1 — начальный', callback_data='diag:claim:a1'),
            InlineKeyboardButton('A2 — элементарный', callback_data='diag:claim:a2'),
        ],
        [
            InlineKeyboardButton('B1 — средний', callback_data='diag:claim:b1'),
            InlineKeyboardButton('B2 — выше среднего', callback_data='diag:claim:b2'),
        ],
        [InlineKeyboardButton('🤷 Не уверен(а)', callback_data='diag:claim:unsure')],
    ])


def diagnostic_challenge_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Да, проверить выше', callback_data='diag:challenge:yes'),
            InlineKeyboardButton('Нет, достаточно', callback_data='diag:challenge:no'),
        ],
    ])


def diagnostic_options_kb(
    options: list[str], *, item_id: int, with_listen: bool = False,
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(opt, callback_data=f'diag:ans:{item_id}:{i}')]
        for i, opt in enumerate(options)
    ]
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
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


def exercise_text_kb(
    *,
    with_hint: bool = False,
    with_ask: bool = True,
    with_listen: bool = False,
) -> InlineKeyboardMarkup:
    rows = []
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
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
    """One CTA — the bot leads through the day step by step."""
    if plan.get('all_done'):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton('🏠 В меню', callback_data='nav:menu')],
        ])
    cta = 'Продолжить' if plan.get('progress_done', 0) > 0 else 'Начать'
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f'▶️ {cta}', callback_data='plan:continue')],
    ])


def progress_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📚 Учиться сегодня', callback_data='plan:menu')],
        [InlineKeyboardButton('🎯 Изменить цель', callback_data='profile:target')],
    ])


def target_level_kb(current: str = '') -> InlineKeyboardMarkup:
    rows = []
    for code, label in (
        ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2'),
    ):
        mark = '✓ ' if current == code else ''
        rows.append([
            InlineKeyboardButton(f'{mark}{label}', callback_data=f'target:set:{code}'),
        ])
    rows.append([InlineKeyboardButton('◀️ Назад', callback_data='profile:back')])
    return InlineKeyboardMarkup(rows)


def skill_focus_kb(selected: set[str] | None = None) -> InlineKeyboardMarkup:
    selected = selected or set()
    labels = {
        'speaking': '🎙️ Говорение',
        'listening': '👂 Аудирование',
        'reading': '📖 Чтение',
        'writing': '✍️ Письмо',
        'grammar': '📐 Грамматика',
        'vocabulary': '🗂 Слова',
    }
    rows = []
    for skill, label in labels.items():
        mark = '✓ ' if skill in selected else ''
        rows.append([
            InlineKeyboardButton(f'{mark}{label}', callback_data=f'focus:toggle:{skill}'),
        ])
    rows.append([InlineKeyboardButton('✅ Готово', callback_data='profile:back')])
    return InlineKeyboardMarkup(rows)


def warmup_kb(quiz: dict | None = None) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton('🔊 Слушать', callback_data='plan:warmup:listen')]]
    if quiz and quiz.get('options'):
        for i, opt in enumerate(quiz['options'][:4]):
            label = opt if len(opt) <= 42 else opt[:39] + '…'
            rows.append([InlineKeyboardButton(label, callback_data=f'plan:warmup:ans:{i}')])
    return InlineKeyboardMarkup(rows)


def schedule_minutes_kb(selected: int = 0) -> InlineKeyboardMarkup:
    choices = [20, 30, 60]
    rows = []
    for m in choices:
        mark = '✓ ' if m == selected else ''
        rows.append([
            InlineKeyboardButton(f'{mark}{m} мин / день', callback_data=f'schedule:min:{m}'),
        ])
    return InlineKeyboardMarkup(rows)


def schedule_days_kb(selected: int = 0) -> InlineKeyboardMarkup:
    rows = []
    for d in (3, 4, 5, 6, 7):
        mark = '✓ ' if d == selected else ''
        rows.append([
            InlineKeyboardButton(f'{mark}{d} дней в неделю', callback_data=f'schedule:days:{d}'),
        ])
    return InlineKeyboardMarkup(rows)


def schedule_edit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('⏱ Время в день', callback_data='profile:schedule:min')],
        [InlineKeyboardButton('📅 Дней в неделю', callback_data='profile:schedule:days')],
        [InlineKeyboardButton('◀️ Назад', callback_data='profile:back')],
    ])


def listening_kb(options: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton('🔊 Слушать диалог', callback_data='plan:listening:listen')]]
    for i, opt in enumerate(options[:4]):
        label = opt if len(opt) <= 42 else opt[:39] + '…'
        rows.append([InlineKeyboardButton(label, callback_data=f'plan:listening:ans:{i}')])
    return InlineKeyboardMarkup(rows)


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
        [InlineKeyboardButton('🎯 Тренировать', callback_data=f'rules:train:{rule_key}')],
        [InlineKeyboardButton('◀️ К карте правил', callback_data='rules:map')],
    ]
    return InlineKeyboardMarkup(rows)


def mistake_rule_kb(rule_key: str, status: str) -> InlineKeyboardMarkup:
    """After tutor spots a grammar mistake — tablet + actions."""
    if status in ('learned', 'known'):
        save_btn = InlineKeyboardButton(
            '🔄 Повторить в библиотеке', callback_data=f'rules:view:{rule_key}',
        )
    else:
        save_btn = InlineKeyboardButton(
            '✅ Добавить в библиотеку', callback_data=f'rule:learn:{rule_key}',
        )
    return InlineKeyboardMarkup([
        [save_btn],
        [InlineKeyboardButton('🎯 Тренировать', callback_data=f'rules:train:{rule_key}')],
        [InlineKeyboardButton('📖 Открыть правило', callback_data=f'rules:view:{rule_key}')],
    ])


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
            [InlineKeyboardButton('⏱ План на день', callback_data='profile:schedule')],
            [InlineKeyboardButton('🎯 Цель уровня', callback_data='profile:target')],
            [InlineKeyboardButton('💪 Фокус практики', callback_data='profile:focus')],
            [InlineKeyboardButton('🗺 Карта пути', callback_data='profile:roadmap')],
            [InlineKeyboardButton('🔔 Напоминания', callback_data='profile:notify')],
            [InlineKeyboardButton('🔁 Пройти диагностику заново', callback_data='profile:rediag')],
        ]
    )


def interests_kb(
    items: list[dict],
    selected: set[int],
    *,
    has_custom: bool = False,
) -> InlineKeyboardMarkup:
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
    custom_mark = '✅ ' if has_custom else ''
    rows.append([InlineKeyboardButton(
        f'{custom_mark}✍️ Написать свои интересы',
        callback_data='intr:custom',
    )])
    rows.append([InlineKeyboardButton('Далее →', callback_data='intr:done')])
    return InlineKeyboardMarkup(rows)


def sphere_kb(spheres: list[dict], selected: str = '') -> InlineKeyboardMarkup:
    """spheres: [{'code','label'}]. Custom sphere always on its own row."""
    rows = []
    row: list[InlineKeyboardButton] = []
    custom: dict | None = None
    for s in spheres:
        if s['code'] == 'other':
            custom = s
            continue
        mark = '✅ ' if s['code'] == selected else ''
        row.append(InlineKeyboardButton(
            f'{mark}{s["label"]}', callback_data=f'sph:set:{s["code"]}',
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if custom:
        mark = '✅ ' if custom['code'] == selected else ''
        rows.append([InlineKeyboardButton(
            f'{mark}{custom["label"]}', callback_data='sph:set:other',
        )])
    return InlineKeyboardMarkup(rows)


def goal_kb(goals: list[dict], selected: str = '') -> InlineKeyboardMarkup:
    """goals: [{'code','label'}]. Custom goal always on its own row."""
    rows = []
    row: list[InlineKeyboardButton] = []
    custom: dict | None = None
    for g in goals:
        if g['code'] == 'other':
            custom = g
            continue
        mark = '✅ ' if g['code'] == selected else ''
        row.append(InlineKeyboardButton(
            f'{mark}{g["label"]}', callback_data=f'goal:set:{g["code"]}',
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if custom:
        mark = '✅ ' if custom['code'] == selected else ''
        rows.append([InlineKeyboardButton(
            f'{mark}{custom["label"]}', callback_data='goal:set:other',
        )])
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


def paywall_kb(plans: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for plan in plans:
        if plan.get('plan_kind') != 'subscription':
            continue
        label = f'{plan["name"]} — {plan["price_rub"]} ₽'
        rows.append([
            InlineKeyboardButton(label, callback_data=f'buy:{plan["code"]}'),
        ])
    rows.append([InlineKeyboardButton('ℹ️ Условия', callback_data='terms')])
    return InlineKeyboardMarkup(rows)


def subscription_kb(*, has_subscription: bool, voice_remaining: int = 0) -> InlineKeyboardMarkup:
    rows = []
    if has_subscription and voice_remaining <= 15:
        rows.append([
            InlineKeyboardButton('+100 мин голоса — 290 ₽', callback_data='buy:voice_100'),
        ])
    if not has_subscription:
        rows.append([InlineKeyboardButton('⭐️ Выбрать тариф', callback_data='paywall:plans')])
    rows.append([InlineKeyboardButton('ℹ️ Условия', callback_data='terms')])
    return InlineKeyboardMarkup(rows)
