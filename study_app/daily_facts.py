"""Copyright-safe daily warmups for reminders (bilingual).

Each item has ``kind``: ``phrase`` (Фраза дня) or ``fact`` (Факт дня).
"""

from __future__ import annotations

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


def warmup_label(kind: str) -> tuple[str, str]:
    return WARMUP_LABELS.get(kind, WARMUP_LABELS['fact'])


GREETING_VARIANTS = [
    'Привет, {name}! Сегодня у тебя живой план — без выбора уроков, всё уже готово.',
    '{name}, доброе утро! Я собрал твою тренировку на сегодня.',
    'С возвращением, {name}! Вот твой персональный чеклист на день.',
    '{name}, пора к английскому — план под твой уровень и интересы ждёт.',
]
