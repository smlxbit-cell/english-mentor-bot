"""Telegram keyboards (inline for flow actions, reply for the main menu)."""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

# Reply-menu: только 2 главные кнопки (остальное — Menu / команды).
BTN_START = '▶️ Начать'
BTN_CONTINUE = '▶️ Продолжить'
BTN_TRAINING = '🎯 Тренировка'

# Legacy — для старых клавиатур и совместимости.
BTN_LEARN = BTN_START
BTN_PROFILE = '👤 Профиль'
BTN_PROGRESS = '📊 Прогресс'
BTN_WORDS = '🗂 Словарь'
BTN_RULES = '📖 Правила'
BTN_TUTOR = '💬 Наставник'
BTN_SUBSCRIBE = '⭐️ Подписка'

PRIMARY_BUTTONS = frozenset({BTN_START, BTN_CONTINUE, BTN_LEARN})

SKILL_FOCUS_RU = {
    'speaking': 'говорение',
    'listening': 'аудирование',
    'reading': 'чтение',
    'writing': 'письмо',
    'grammar': 'грамматика',
    'vocabulary': 'слова',
}


def main_menu(*, continue_mode: bool = False) -> ReplyKeyboardMarkup:
    """Две кнопки в одну строку: урок + тренировка."""
    primary = BTN_CONTINUE if continue_mode else BTN_START
    return ReplyKeyboardMarkup(
        [[primary, BTN_TRAINING]],
        resize_keyboard=True,
    )


def training_menu_kb() -> InlineKeyboardMarkup:
    """Подменю «Тренировка»: слова, правила, AI-наставник."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('📚 Слова', callback_data='train:words'),
            InlineKeyboardButton('🎓 Правила', callback_data='train:rules'),
        ],
        [InlineKeyboardButton('💬 AI · Наставник', callback_data='train:tutor')],
    ])


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
        [InlineKeyboardButton('C1 — продвинутый+', callback_data='diag:claim:c1')],
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
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('💡 Объяснить', callback_data=f'diag:explain:{item_id}'),
        InlineKeyboardButton('➡️ Дальше', callback_data='diag:continue'),
    ]])


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
        rows.append([
            InlineKeyboardButton('🔊 Слушать', callback_data='tts:dict'),
            InlineKeyboardButton('🎯 Тренировка', callback_data='srs:start'),
        ])
    rows.append([InlineKeyboardButton('← Слова', callback_data='words:hub')])
    return InlineKeyboardMarkup(rows)


def word_hub_kb(*, due_count: int = 0, unseen_total: int = 0) -> InlineKeyboardMarkup:
    """Hub: Практика | Новые | Мои слова — одна строка, короткие подписи."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('🎯 Практика', callback_data='words:repeat'),
            InlineKeyboardButton('📘 Словарь', callback_data='words:new'),
            InlineKeyboardButton('📗 Мои слова', callback_data='words:mydict'),
        ],
    ])


def word_new_section_kb(*, daily: int = 10) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f'Начать · {daily}', callback_data='words:learn:daily'),
            InlineKeyboardButton('📖 Из словаря', callback_data='words:new:pick'),
        ],
        [InlineKeyboardButton('← Слова', callback_data='words:hub')],
    ])


def word_new_pick_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('📊 Уровни', callback_data='words:bank'),
            InlineKeyboardButton('👀 Знаю?', callback_data='words:survey:menu'),
            InlineKeyboardButton('🔍 Поиск', callback_data='words:search'),
        ],
        [InlineKeyboardButton('← Слова', callback_data='words:hub')],
    ])


def word_daily_intro_card_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('🎯 Учить', callback_data='words:intro:next'),
            InlineKeyboardButton('✅ Знаю', callback_data='words:intro:known'),
        ],
        [InlineKeyboardButton('← Выход', callback_data='words:intro:stop')],
    ])


def word_drill_choice_kb(options: list[str], *, step: str) -> InlineKeyboardMarkup:
    rows = []
    for i, opt in enumerate(options):
        label = opt if len(opt) <= 36 else f'{opt[:35]}…'
        rows.append([InlineKeyboardButton(label, callback_data=f'wd:pick:{step}:{i}')])
    if step == 'listening':
        rows.append([InlineKeyboardButton('👀 Показать слово', callback_data='wd:hint')])
    if step == 'context':
        rows.append([InlineKeyboardButton('🇷🇺 Переводы вариантов', callback_data='wd:hint')])
    return InlineKeyboardMarkup(rows)


def word_drill_continue_kb(*, show_words: bool = True) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton('Дальше →', callback_data='wd:cont')]]
    if show_words:
        rows.append([InlineKeyboardButton('📖 Все слова', callback_data='wd:words')])
    return InlineKeyboardMarkup(rows)


def word_drill_recall_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('💡 Подсказка', callback_data='wd:hint')],
    ])


def word_daily_intro_finish_kb(*, count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f'🎯 Тренировка · {count}', callback_data='words:learn:quiz')],
        [InlineKeyboardButton('🔊 Слушать все', callback_data='tts:say')],
        [InlineKeyboardButton('← Слова', callback_data='words:hub')],
    ])


def word_survey_levels_kb(user_level: str) -> InlineKeyboardMarkup:
    def lbl(level: str) -> str:
        u = level.upper()
        return f'{u} ★' if level.lower() == (user_level or 'a1').lower() else u

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lbl('a1'), callback_data='words:survey:level:a1'),
            InlineKeyboardButton(lbl('a2'), callback_data='words:survey:level:a2'),
            InlineKeyboardButton(lbl('b1'), callback_data='words:survey:level:b1'),
            InlineKeyboardButton(lbl('b2'), callback_data='words:survey:level:b2'),
            InlineKeyboardButton(lbl('c1'), callback_data='words:survey:level:c1'),
        ],
        [InlineKeyboardButton('← Словарь', callback_data='words:new')],
    ])


def word_repeat_section_kb(*, due: int = 0) -> InlineKeyboardMarkup:
    rows = []
    if due:
        rows.append([
            InlineKeyboardButton(f'🎯 Начать · {due}', callback_data='srs:start'),
        ])
    rows.append([InlineKeyboardButton('← Слова', callback_data='words:hub')])
    return InlineKeyboardMarkup(rows)


def word_dict_hub_kb(*, learning_count: int = 0) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton('📗 Учить', callback_data='words:dict:learning:0'),
            InlineKeyboardButton('✅ Уже знаю', callback_data='words:dict:known:0'),
        ],
        [
            InlineKeyboardButton('📁 Темы', callback_data='words:dict:topics'),
            InlineKeyboardButton('📊 Уровни', callback_data='words:dict:levels'),
        ],
    ]
    if learning_count > 0:
        rows.insert(0, [
            InlineKeyboardButton(
                f'🎯 Тренировка · {learning_count}',
                callback_data='srs:start',
            ),
        ])
    rows.append([InlineKeyboardButton('← Слова', callback_data='words:hub')])
    return InlineKeyboardMarkup(rows)


def word_bank_menu_kb(user_level: str = 'a1') -> InlineKeyboardMarkup:
    def lbl(level: str) -> str:
        u = level.upper()
        return f'{u} ★' if level.lower() == (user_level or 'a1').lower() else u

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(lbl('a1'), callback_data='words:bank:level:a1:0'),
            InlineKeyboardButton(lbl('a2'), callback_data='words:bank:level:a2:0'),
            InlineKeyboardButton(lbl('b1'), callback_data='words:bank:level:b1:0'),
            InlineKeyboardButton(lbl('b2'), callback_data='words:bank:level:b2:0'),
            InlineKeyboardButton(lbl('c1'), callback_data='words:bank:level:c1:0'),
        ],
        [InlineKeyboardButton('← Словарь', callback_data='words:new')],
    ])


def word_add_menu_kb(user_level: str = 'a1') -> InlineKeyboardMarkup:
    return word_bank_menu_kb(user_level)


def word_dict_levels_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('A1', callback_data='words:dict:level:a1:0'),
            InlineKeyboardButton('A2', callback_data='words:dict:level:a2:0'),
            InlineKeyboardButton('B1', callback_data='words:dict:level:b1:0'),
            InlineKeyboardButton('B2', callback_data='words:dict:level:b2:0'),
            InlineKeyboardButton('C1', callback_data='words:dict:level:c1:0'),
        ],
        [InlineKeyboardButton('← Мои слова', callback_data='words:mydict')],
    ])


def _word_page_nav_row(
    prefix: str,
    *,
    page: int,
    pages: int,
) -> list[InlineKeyboardButton] | None:
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton('◀️ Назад', callback_data=f'{prefix}:{page - 1}'))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton('▶️ След. стр.', callback_data=f'{prefix}:{page + 1}'))
    return nav or None


def _word_page_training_row(*, learning_count: int) -> list[InlineKeyboardButton] | None:
    if learning_count <= 0:
        return None
    return [InlineKeyboardButton(
        f'🎯 Тренировка · {learning_count}',
        callback_data='srs:start',
    )]


def word_bank_list_page_kb(
    items: list[dict],
    prefix: str,
    *,
    page: int,
    pages: int,
    back_data: str = 'words:bank',
    level: str | None = None,
    topic: str | None = None,
    learning_count: int = 0,
) -> InlineKeyboardMarkup:
    """Bank browse: page training, one-by-one survey, bulk mark, pagination."""
    del learning_count  # page-scoped training only
    rows: list[list[InlineKeyboardButton]] = []
    if items and (level or topic):
        n = len(items)
        if level:
            train_cb = f'words:bank:page:train:{level}:{page}'
            survey_cb = f'words:survey:page:{level}:{page}'
            known_cb = f'words:bank:page:known:{level}:{page}'
            learn_cb = f'words:bank:page:learn:{level}:{page}'
        else:
            train_cb = f'words:bank:page:train:topic:{topic}:{page}'
            survey_cb = None
            known_cb = f'words:bank:page:known:topic:{topic}:{page}'
            learn_cb = f'words:bank:page:learn:topic:{topic}:{page}'
        rows.append([InlineKeyboardButton(
            f'🎯 Тренировка · {n}',
            callback_data=train_cb,
        )])
        if survey_cb:
            rows.append([InlineKeyboardButton('▶️ По одному', callback_data=survey_cb)])
        rows.append([
            InlineKeyboardButton('✅ Знаю', callback_data=known_cb),
            InlineKeyboardButton('🎯 Учить', callback_data=learn_cb),
        ])
    nav = _word_page_nav_row(prefix, page=page, pages=pages)
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton('← Уровни', callback_data=back_data)])
    return InlineKeyboardMarkup(rows)


def word_list_page_kb(
    prefix: str,
    *,
    page: int,
    pages: int,
    back_data: str = 'words:mydict',
    learning_count: int = 0,
    bulk_known_cb: str | None = None,
    bulk_learn_cb: str | None = None,
) -> InlineKeyboardMarkup:
    """Personal dictionary lists: bulk mark, training, pagination."""
    rows: list[list[InlineKeyboardButton]] = []
    train_row = _word_page_training_row(learning_count=learning_count)
    if train_row:
        rows.append(train_row)
    bulk_row: list[InlineKeyboardButton] = []
    if bulk_known_cb:
        bulk_row.append(InlineKeyboardButton(
            '✅ Знаю · вся страница',
            callback_data=bulk_known_cb,
        ))
    if bulk_learn_cb:
        bulk_row.append(InlineKeyboardButton(
            '🎯 Учить · вся страница',
            callback_data=bulk_learn_cb,
        ))
    if bulk_row:
        rows.append(bulk_row)
    nav = _word_page_nav_row(prefix, page=page, pages=pages)
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton('← Назад', callback_data=back_data)])
    return InlineKeyboardMarkup(rows)


def word_bank_hub_kb(user_level: str = 'a1') -> InlineKeyboardMarkup:
    return word_bank_menu_kb(user_level)


def word_bank_topics_kb(topics: list[tuple[str, int]]) -> InlineKeyboardMarkup:
    from learning.word_bank.navigation import canonical_topic, topic_button_label

    rows = []
    row: list[InlineKeyboardButton] = []
    for slug, count in topics[:12]:
        canon = canonical_topic(slug)
        row.append(InlineKeyboardButton(
            topic_button_label(canon, count),
            callback_data=f'words:bank:topic:{canon}:0',
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton('← Словарь', callback_data='words:bank')])
    return InlineKeyboardMarkup(rows)


def word_bank_entry_kb(
    bank_entry_id: int,
    *,
    page_cb: str,
) -> InlineKeyboardMarkup:
    bid = bank_entry_id
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('✅ Знаю', callback_data=f'words:bank:known:{bid}'),
            InlineKeyboardButton('🎯 Учить', callback_data=f'words:bank:learn:{bid}'),
        ],
        [InlineKeyboardButton('← К списку', callback_data=page_cb)],
    ])


def word_search_result_kb(results: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for item in results[:6]:
        label = f'{item["english"][:20]}'
        rows.append([InlineKeyboardButton(
            label,
            callback_data=f'words:bank:open:{item["bank_entry_id"]}',
        )])
    rows.append([InlineKeyboardButton('← Словарь', callback_data='words:bank')])
    return InlineKeyboardMarkup(rows)


def word_survey_kb(bank_entry_id: int) -> InlineKeyboardMarkup:
    bid = bank_entry_id
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('✅ Знаю', callback_data=f'words:survey:known:{bid}'),
            InlineKeyboardButton('🎯 Учить', callback_data=f'words:survey:learn:{bid}'),
        ],
    ])


def word_survey_finish_kb(
    *,
    session_learn_count: int = 0,
    learning_count: int = 0,
    back_data: str | None = None,
) -> InlineKeyboardMarkup:
    del learning_count
    rows = []
    if session_learn_count > 0:
        rows.append([InlineKeyboardButton(
            f'🎯 Тренировка · {session_learn_count}',
            callback_data='words:survey:train',
        )])
    if back_data:
        rows.append([InlineKeyboardButton('← К списку', callback_data=back_data)])
    rows.append([InlineKeyboardButton('← Слова', callback_data='words:hub')])
    return InlineKeyboardMarkup(rows)


def word_intro_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Тренировка', callback_data='words:learn:quiz'),
            InlineKeyboardButton('Слушать', callback_data='tts:say'),
        ],
        [InlineKeyboardButton('← Словарь', callback_data='words:new')],
    ])


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
            [
                InlineKeyboardButton('Сфера', callback_data='profile:sphere'),
                InlineKeyboardButton('Расписание', callback_data='profile:schedule'),
            ],
            [
                InlineKeyboardButton('Цель уровня', callback_data='profile:target'),
                InlineKeyboardButton('Карта пути', callback_data='profile:roadmap'),
            ],
            [
                InlineKeyboardButton('Тест уровня', callback_data='profile:retest'),
                InlineKeyboardButton('Напоминания', callback_data='profile:notify'),
            ],
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


def paywall_kb(
    plans: list[dict],
    *,
    show_free: bool = True,
    has_subscription: bool = False,
    current_plan_code: str = '',
) -> InlineKeyboardMarkup:
    from billing_app.plans_catalog import PLAN_BUTTON_LABELS, plan_button_label

    rows = []
    if show_free:
        rows.append([
            InlineKeyboardButton(
                PLAN_BUTTON_LABELS['free'],
                callback_data='tier:free',
            ),
        ])
    sub_plans = [p for p in plans if p.get('plan_kind') == 'subscription']
    if not has_subscription:
        for plan in sub_plans:
            rows.append([
                InlineKeyboardButton(
                    plan_button_label(plan),
                    callback_data=f'buy:{plan["code"]}',
                ),
            ])
    elif current_plan_code == 'basic':
        rows.append([
            InlineKeyboardButton(
                PLAN_BUTTON_LABELS['upgrade_pro'],
                callback_data='buy:upgrade:pro',
            ),
        ])
    addon_cb = 'buy:voice_100' if has_subscription else 'addon:info'
    rows.append([
        InlineKeyboardButton(PLAN_BUTTON_LABELS['voice_100'], callback_data=addon_cb),
        InlineKeyboardButton('ℹ️ Условия', callback_data='terms'),
    ])
    return InlineKeyboardMarkup(rows)


def subscription_kb(
    *,
    has_subscription: bool,
    voice_remaining: int = 0,
    plan_code: str = '',
) -> InlineKeyboardMarkup:
    from billing_app.plans_catalog import PLAN_BUTTON_LABELS

    rows = []
    if has_subscription:
        if plan_code == 'basic':
            rows.append([
                InlineKeyboardButton(
                    PLAN_BUTTON_LABELS['upgrade_pro'],
                    callback_data='buy:upgrade:pro',
                ),
            ])
        rows.append([
            InlineKeyboardButton(
                PLAN_BUTTON_LABELS['voice_100'],
                callback_data='buy:voice_100',
            ),
            InlineKeyboardButton('ℹ️ Условия', callback_data='terms'),
        ])
    else:
        rows.append([
            InlineKeyboardButton('💳 Тарифы', callback_data='paywall:plans'),
            InlineKeyboardButton(
                PLAN_BUTTON_LABELS['voice_100'],
                callback_data='addon:info',
            ),
        ])
        rows.append([InlineKeyboardButton('ℹ️ Условия оплаты', callback_data='terms')])
    return InlineKeyboardMarkup(rows)
