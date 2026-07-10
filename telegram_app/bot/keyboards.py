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

SKILL_FOCUS_RU = {
    'speaking': 'говорение',
    'listening': 'аудирование',
    'reading': 'чтение',
    'writing': 'письмо',
    'grammar': 'грамматика',
    'vocabulary': 'слова',
}


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
        [InlineKeyboardButton('C1 — продвинутый', callback_data='diag:claim:c1')],
        [InlineKeyboardButton('🤷 Не уверен(а)', callback_data='diag:claim:unsure')],
    ])


def diagnostic_challenge_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Проверить уровень выше', callback_data='diag:challenge:yes')],
        [InlineKeyboardButton('Пропустить', callback_data='diag:challenge:no')],
    ])


def diagnostic_options_kb(
    options: list[str], *, item_id: int, with_listen: bool = False,
    with_dont_know: bool = True,
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(opt, callback_data=f'diag:ans:{item_id}:{i}')]
        for i, opt in enumerate(options)
    ]
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
    if with_dont_know:
        rows.append([InlineKeyboardButton('🤔 Не знаю', callback_data=f'diag:idk:{item_id}')])
    return InlineKeyboardMarkup(rows)


def diagnostic_text_kb(item_id: int, *, with_listen: bool = False) -> InlineKeyboardMarkup:
    """For typed diagnostic answers (fill/translation): a 'don't know' escape."""
    rows = []
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
    rows.append([InlineKeyboardButton('🤔 Не знаю', callback_data=f'diag:idk:{item_id}')])
    return InlineKeyboardMarkup(rows)


def diagnostic_review_kb(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('💡 Объяснить', callback_data=f'diag:explain:{item_id}')],
        [InlineKeyboardButton('➡️ Дальше', callback_data='diag:continue')],
    ])


def diagnostic_wrong_kb(item_id: int) -> InlineKeyboardMarkup:
    return diagnostic_review_kb(item_id)


def diagnostic_continue_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('➡️ Дальше', callback_data='diag:continue')],
    ])


def skill_test_offer_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🧪 Пройти тест (~5 мин)', callback_data='skilltest:start')],
        [InlineKeyboardButton('Пропустить — выберу сам', callback_data='skilltest:skip')],
    ])


def skill_test_options_kb(
    options: list[str], *, with_listen: bool = False,
    with_dont_know: bool = True,
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(opt, callback_data=f'skilltest:ans:{i}')]
        for i, opt in enumerate(options)
    ]
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать ещё раз', callback_data='tts:say')])
    if with_dont_know:
        rows.append([InlineKeyboardButton('🤔 Не знаю', callback_data='skilltest:idk')])
    return InlineKeyboardMarkup(rows)


def skill_test_text_kb(*, with_listen: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
    rows.append([InlineKeyboardButton('🤔 Не знаю', callback_data='skilltest:idk')])
    return InlineKeyboardMarkup(rows)


def skill_test_result_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('👉 Настроить фокус практики', callback_data='skilltest:focus')],
    ])


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
    with_skip: bool = False,
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
    if with_skip:
        rows.append([InlineKeyboardButton('⏭ Слишком просто', callback_data='lesson:skip')])
    return InlineKeyboardMarkup(rows)


def exercise_text_kb(
    *,
    with_hint: bool = False,
    with_ask: bool = True,
    with_listen: bool = False,
    with_skip: bool = False,
) -> InlineKeyboardMarkup:
    rows = []
    if with_listen:
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
    if with_hint:
        rows.append([InlineKeyboardButton('💡 Подсказка', callback_data='ex:hint')])
    if with_ask:
        rows.append([InlineKeyboardButton('💬 Спросить', callback_data='lesson:ask')])
    if with_skip:
        rows.append([InlineKeyboardButton('⏭ Слишком просто', callback_data='lesson:skip')])
    return InlineKeyboardMarkup(rows) if rows else None


def grammar_rule_compact_kb(rule_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🔊 Слушать примеры', callback_data='tts:step')],
        [
            InlineKeyboardButton('✅ Выучил', callback_data=f'rule:learn:{rule_key}'),
            InlineKeyboardButton('👌 Уже знаю', callback_data=f'rule:known:{rule_key}'),
        ],
        [InlineKeyboardButton('➡️ Далее', callback_data='lesson:next')],
    ])


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


def target_level_kb(current: str = '', *, onboarding: bool = False) -> InlineKeyboardMarkup:
    # Bot tops out at confident C1 — no C2 track for now.
    rows = [[
        InlineKeyboardButton(f'{"✓ " if current == code else ""}{code}',
                             callback_data=f'target:set:{code}')
        for code in ('B1', 'B2', 'C1')
    ]]
    if not onboarding:
        rows.append([InlineKeyboardButton('◀️ Назад', callback_data='profile:back')])
    return InlineKeyboardMarkup(rows)


def skill_focus_kb(selected: set[str] | None = None, *, onboarding: bool = False) -> InlineKeyboardMarkup:
    selected = selected or set()
    labels = [
        ('speaking', '🎙 Говорение'),
        ('listening', '👂 Аудирование'),
        ('reading', '📖 Чтение'),
        ('writing', '✍️ Письмо'),
        ('grammar', '📐 Грамматика'),
        ('vocabulary', '🗂 Слова'),
    ]
    rows = []
    for i in range(0, len(labels), 2):
        row = []
        for skill, label in labels[i:i + 2]:
            mark = '✅ ' if skill in selected else ''
            row.append(
                InlineKeyboardButton(f'{mark}{label}', callback_data=f'focus:toggle:{skill}')
            )
        rows.append(row)
    done_cb = 'focus:done' if onboarding else 'profile:back'
    rows.append([InlineKeyboardButton('➡️ Подтвердить выбор', callback_data=done_cb)])
    return InlineKeyboardMarkup(rows)


def speaking_anxiety_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('😰 Да, мне сложно говорить', callback_data='anxiety:set:high')],
        [InlineKeyboardButton('😅 Немного волнуюсь', callback_data='anxiety:set:mild')],
        [InlineKeyboardButton('😊 Нет, всё ок', callback_data='anxiety:set:none')],
    ])


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


WEEKDAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
WEEKDAY_NAMES_FULL = [
    'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье',
]


def rest_day_kb(selected: int | None = 6) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, 7, 3):
        row = []
        for d in range(i, min(i + 3, 7)):
            mark = '✓ ' if d == selected else ''
            row.append(InlineKeyboardButton(
                f'{mark}{WEEKDAY_NAMES[d]}', callback_data=f'schedule:rest:{d}'))
        rows.append(row)
    none_mark = '✓ ' if (selected is None or selected == 7) else ''
    rows.append([InlineKeyboardButton(
        f'{none_mark}Без выходного', callback_data='schedule:rest:7')])
    return InlineKeyboardMarkup(rows)


def schedule_edit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('⏱ Время в день', callback_data='profile:schedule:min')],
        [InlineKeyboardButton('📅 Дней в неделю', callback_data='profile:schedule:days')],
        [InlineKeyboardButton('🌿 День отдыха', callback_data='profile:schedule:rest')],
        [InlineKeyboardButton('◀️ Назад', callback_data='profile:back')],
    ])


def listening_kb(options: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton('🔊 Слушать диалог', callback_data='plan:listening:listen')]]
    for i, opt in enumerate(options[:4]):
        label = opt if len(opt) <= 42 else opt[:39] + '…'
        rows.append([InlineKeyboardButton(label, callback_data=f'plan:listening:ans:{i}')])
    return InlineKeyboardMarkup(rows)


def speaking_bite_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🔊 Пример ответа', callback_data='plan:speaking:listen')],
        [InlineKeyboardButton('⏭ Пропустить', callback_data='plan:speaking:skip')],
    ])


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
