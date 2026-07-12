"""Copyright-safe daily warmups, greetings, and reminder copy (bilingual).

Each fact item has ``kind``: ``phrase`` (Фраза дня) or ``fact`` (Факт дня).
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime

DAILY_FACTS: list[dict] = [
    {
        'kind': 'fact',
        'ru': 'В английском «please» и «thank you» — не формальность, а норма общения.',
        'en': 'In English, "please" and "thank you" are everyday politeness, not extra formality.',
    },
    {
        'kind': 'fact',
        'ru': 'Слово «queue» (очередь) — одно из самых «британских» слов в языке.',
        'en': 'The word "queue" is one of the most British words in English.',
    },
    {
        'kind': 'fact',
        'ru': 'Мозг запоминает язык быстрее, когда вы говорите вслух — даже с ошибками.',
        'en': 'Your brain learns a language faster when you speak out loud — even with mistakes.',
    },
    {
        'kind': 'phrase',
        'ru': '«Small talk» — короткий светский разговор. Он открывает двери к настоящему общению.',
        'en': 'Small talk is light conversation. It opens the door to real connection.',
    },
    {
        'kind': 'fact',
        'ru': 'В UK чаще говорят «lift», в US — «elevator». Оба варианта правильные.',
        'en': 'In the UK people say "lift"; in the US they say "elevator". Both are correct.',
    },
    {
        'kind': 'phrase',
        'ru': 'Фраза «How are you?» часто риторическая — достаточно ответить «Good, thanks!»',
        'en': '"How are you?" is often rhetorical — "Good, thanks!" is enough.',
    },
    {
        'kind': 'fact',
        'ru': '15 минут в день стабильнее, чем 2 часа раз в неделю — так работает привычка.',
        'en': 'Fifteen minutes a day beats two hours once a week — that is how habits work.',
    },
    {
        'kind': 'phrase',
        'ru': '«Would like» звучит мягче, чем «want» — особенно в кафе и на работе.',
        'en': '"Would like" sounds softer than "want" — especially in cafés and at work.',
    },
    {
        'kind': 'fact',
        'ru': 'Английский — язык 1,5 млрд людей. Каждый день вы добавляете себя к этому числу.',
        'en': 'English is spoken by 1.5 billion people. Every day you join that number.',
    },
    {
        'kind': 'fact',
        'ru': 'Слушать короткие фразы по 10–20 секунд — отличная тренировка для уха.',
        'en': 'Listening to short 10–20 second phrases is great ear training.',
    },
]

WARMUP_LABELS = {
    'phrase': ('💬', 'Фраза дня'),
    'fact': ('💡', 'Факт дня'),
}

# Bodies without time-of-day — paired with time_greeting_ru(hour).
PLAN_GREETING_BODIES = [
    'Я собрал твою тренировку на сегодня.',
    'Вот персональный чеклист — всё готово, без выбора уроков.',
    'План под твой уровень ждёт — поведу по шагам.',
    'Тренировка на сегодня готова — начнём, когда удобно.',
    'Свежий маршрут на день: эпизод, практика и немного теории.',
    'Твой план уже собран — осталось нажать «Начать».',
    'Небольшая глава дня — реальный прогресс за пару десятков минут.',
    'Живой план без лишнего выбора — просто иди по шагам.',
]

REST_GREETING_BODIES = [
    'Сегодня день отдыха — лёгкая разминка и всё 🌿',
    'В плане день отдыха. Отдохни — прогресс не сгорит.',
    'Сегодня без нового эпизода — только мягкая разминка.',
]

REMINDER_OPENERS = [
    'Привет, {name}! 👋',
    '{name}, на связи Spirit ✨',
    'Эй, {name}!',
    '{name}, короткое напоминание 👇',
    'Привет, {name}!',
]

REMINDER_NUDGES = [
    'Пора к английскому — план на сегодня уже ждёт.',
    'Небольшая тренировка сейчас = увереннее потом.',
    'Время для английского — всего несколько минут в плюс к цели.',
    'Загляни в план дня — там твой маршрут на сегодня.',
    'Пару шагов по плану — и день не зря для языка.',
    'Английский любит регулярность. Сегодняшний план готов.',
    'Spirit напоминает: тренировка на сегодня собрана 🎯',
    'Маленький шаг каждый день — большой результат со временем.',
]

REMINDER_MICRO_QUOTES = [
    '💬 «Practice makes progress» — практика двигает вперёд.',
    '💬 «One day or day one» — сегодня может быть тот самый день.',
    '💬 15 минут стабильнее, чем 2 часа раз в неделю.',
    '💬 Говорить вслух — даже с ошибками — ускоряет память.',
    '💬 Small talk открывает двери к настоящему общению.',
    '💬 «Would like» мягче, чем «want» — пригодится в жизни.',
]


def warmup_label(kind: str) -> tuple[str, str]:
    return WARMUP_LABELS.get(kind, WARMUP_LABELS['fact'])


def _day_seed(user_id: int, day: date, *, salt: str = '') -> int:
    raw = f'{salt}:{user_id}:{day.isoformat()}'.encode()
    return int(hashlib.sha256(raw).hexdigest(), 16)


def time_greeting_ru(hour: int) -> str:
    """Time-of-day phrase in Russian (0–23)."""
    if 5 <= hour < 12:
        return 'доброе утро'
    if 12 <= hour < 17:
        return 'добрый день'
    if 17 <= hour < 23:
        return 'добрый вечер'
    return 'привет'


def pick_plan_greeting(
    name: str,
    user_id: int,
    day: date,
    *,
    rest: bool = False,
    now: datetime | None = None,
) -> str:
    """Personalized plan opener matching the current time of day."""
    from django.utils import timezone

    now = now or timezone.localtime()
    hour = now.hour
    display = (name or 'друг').strip()
    time_phrase = time_greeting_ru(hour)

    if rest:
        bodies = REST_GREETING_BODIES
        seed = _day_seed(user_id, day, salt='rest')
    else:
        bodies = PLAN_GREETING_BODIES
        seed = _day_seed(user_id, day, salt='plan')

    body = bodies[seed % len(bodies)]
    # Night: neutral «привет» reads better without «!» formality
    if time_phrase == 'привет':
        return f'{display}, {time_phrase}! {body}'
    return f'{display}, {time_phrase}! {body}'


def pick_reminder_lines(
    name: str,
    user_id: int,
    day: date,
    hour: int,
    *,
    include_quote: bool = True,
) -> list[str]:
    """Varied reminder opener + nudge (+ optional micro-quote)."""
    display = (name or 'друг').strip()
    seed = _day_seed(user_id, day, salt=f'remind:{hour}')
    opener = REMINDER_OPENERS[seed % len(REMINDER_OPENERS)].format(name=display)
    nudge = REMINDER_NUDGES[(seed // 5) % len(REMINDER_NUDGES)]
    lines = [opener, nudge]
    if include_quote:
        quote = REMINDER_MICRO_QUOTES[(seed // 11) % len(REMINDER_MICRO_QUOTES)]
        lines.extend(['', quote])
    return lines


# Legacy export — kept for imports; prefer pick_plan_greeting.
GREETING_VARIANTS = PLAN_GREETING_BODIES
