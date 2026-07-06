"""Tips and quotes for inactive-user re-engagement messages."""

from __future__ import annotations

INACTIVE_NUDGE_DAYS = 7

# Practical language-learning advice (RU) + short EN line for mood.
INACTIVE_TIPS: list[dict[str, str]] = [
    {
        'tip': 'Не бойся ошибок — они показывают, где расти. '
               'Лучше сказать неидеально, чем молчать.',
        'en': 'Mistakes mean you are trying.',
    },
    {
        'tip': 'Выбирай темы, которые тебе правда интересны: '
               'сериалы, работа, путешествия. Так легче запоминать слова.',
        'en': 'Learn what you love — it sticks.',
    },
    {
        'tip': 'Встрой английский в быт: подписи в телефоне, '
               '1 подкаст за завтраком, 3 слова перед сном.',
        'en': 'Small daily habits beat rare marathons.',
    },
    {
        'tip': '10 минут каждый день лучше, чем 2 часа раз в месяц. '
               'Мозгу нужна регулярность, не подвиг.',
        'en': 'Consistency beats intensity.',
    },
    {
        'tip': 'Повторяй вслух — даже шёпотом. '
               'Губы и уши тренируют память так же, как глаза.',
        'en': 'Say it out loud, even quietly.',
    },
    {
        'tip': 'Не переводи каждое слово в голове. '
               'Сначала смысл фразы, потом детали.',
        'en': 'Get the message first, words second.',
    },
    {
        'tip': 'Записывай 3 новых слова в день и используй их в одном предложении. '
               'Три — это уже прогресс.',
        'en': 'Three new words a day add up fast.',
    },
    {
        'tip': 'Смотри короткие клипы с субтитрами на EN — '
               'ухо привыкает к живой речи.',
        'en': 'Train your ear with real speech.',
    },
    {
        'tip': 'Если страшно говорить — начни с чата или голосовых себе. '
               'Никто не оценивает, пока ты учишься.',
        'en': 'Progress, not perfection.',
    },
    {
        'tip': 'Связывай новое слово с картинкой или эмоцией — '
               'мозг любит истории, не списки.',
        'en': 'Link words to images and feelings.',
    },
    {
        'tip': 'После урока задай себе один вопрос на английском — '
               'What did I learn today?',
        'en': 'One question closes the loop.',
    },
    {
        'tip': 'Не сравнивай себя с другими. Сравнивай с собой вчерашней.',
        'en': 'You are your only competition.',
    },
    {
        'tip': 'Ошибка в грамматике не отменяет разговор. '
               'Тебя поймут — главное сказать.',
        'en': 'Communication comes first.',
    },
    {
        'tip': 'Поставь телефон на английский на 1 час в день — '
               'мелочь, а мозг привыкает.',
        'en': 'Immersion can be tiny.',
    },
    {
        'tip': 'Вернись к одному незаконченному эпизоду — '
               'закрытый круг даёт энергию на новое.',
        'en': 'Finish one thing, then start fresh.',
    },
]

MOTIVATIONAL_LINES = [
    'The only way to learn is to start again.',
    'Every day is Day 1 — in a good way.',
    'You do not have to be great to start.',
    'Language is a gym for your brain.',
    'Come back — your story continues.',
]


def pick_inactive_tip(user_id: int, days_away: int) -> dict[str, str]:
    tip = INACTIVE_TIPS[(user_id + days_away) % len(INACTIVE_TIPS)]
    quote = MOTIVATIONAL_LINES[(user_id * 3 + days_away) % len(MOTIVATIONAL_LINES)]
    return {**tip, 'quote': quote}


def days_label_ru(n: int) -> str:
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return f'{n} день'
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f'{n} дня'
    return f'{n} дней'
