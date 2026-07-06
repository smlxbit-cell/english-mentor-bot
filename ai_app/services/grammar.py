"""Deterministic grammar explanations (0 tokens).

The tutor tries these canned, high-quality explanations first; only questions
that don't match fall through to the AI. This keeps the most common grammar
questions free and instant.
"""

from __future__ import annotations

# Each entry: (keywords that trigger it, explanation in Russian with EN examples).
_TOPICS: list[tuple[tuple[str, ...], str]] = [
    (
        ('present simple', 'презент симпл', 'настоящее простое', 'presents simple'),
        '📘 Present Simple — регулярные действия и факты.\n'
        '• I/you/we/they + глагол: I work.\n'
        '• he/she/it + глагол+s: She works.\n'
        '• Вопрос/отрицание через do/does: Do you work? He doesn\'t work.\n'
        'Пример: She goes to school every day.',
    ),
    (
        ('present continuous', 'континиус', 'презент континиус', 'сейчас происходит'),
        '📘 Present Continuous — действие прямо сейчас.\n'
        '• am/is/are + глагол-ing: I am reading. They are playing.\n'
        'Маркеры: now, at the moment.\n'
        'Пример: I am learning English now.',
    ),
    (
        ('past simple', 'паст симпл', 'прошедшее простое', 'прошедшее время'),
        '📘 Past Simple — завершённое действие в прошлом.\n'
        '• Правильные глаголы +ed: worked, played.\n'
        '• Неправильные — 2-я форма: go→went, see→saw.\n'
        '• Вопрос/отрицание через did: Did you go? I didn\'t go.\n'
        'Пример: We visited London last year.',
    ),
    (
        ('present perfect', 'презент перфект', 'have done', 'perfect'),
        '📘 Present Perfect — связь прошлого с настоящим (результат/опыт).\n'
        '• have/has + 3-я форма: I have finished. She has gone.\n'
        'Маркеры: just, already, yet, ever, never, since, for.\n'
        'Пример: I have just eaten.',
    ),
    (
        ('article', 'артикл', 'a ', 'an ', 'the ', 'артикли'),
        '📘 Артикли a/an/the.\n'
        '• a/an — что-то одно и неопределённое: a cat, an apple (an перед гласным звуком).\n'
        '• the — что-то конкретное/уже известное: the sun, the book on the table.\n'
        'Пример: I saw a dog. The dog was big.',
    ),
    (
        ('plural', 'множественное', 'множественного', 'plurals'),
        '📘 Множественное число.\n'
        '• Обычно +s: cat→cats.\n'
        '• +es после s, x, ch, sh: box→boxes.\n'
        '• y→ies: city→cities.\n'
        'Исключения: man→men, child→children, foot→feet.',
    ),
    (
        ('comparative', 'сравнительная', 'superlative', 'превосходная', 'сравнение'),
        '📘 Сравнение прилагательных.\n'
        '• Короткие: +er/+est: big→bigger→the biggest.\n'
        '• Длинные: more/most: more beautiful, the most beautiful.\n'
        'Исключения: good→better→best, bad→worse→worst.',
    ),
    (
        ('will', 'going to', 'future', 'будущее время', 'будущее'),
        '📘 Будущее время.\n'
        '• will — решение сейчас/прогноз: I will help you.\n'
        '• be going to — план/намерение: I am going to travel.\n'
        'Пример: It will rain. I\'m going to study tonight.',
    ),
    (
        ('modal', 'can', 'could', 'must', 'should', 'модальн'),
        '📘 Модальные глаголы.\n'
        '• can — умение/возможность: I can swim.\n'
        '• must — необходимость: You must stop.\n'
        '• should — совет: You should rest.\n'
        'После модального — глагол без to и без -s.',
    ),
    (
        ('preposition', 'предлог', 'in on at', 'предлоги времени'),
        '📘 Предлоги времени in/on/at.\n'
        '• at — точное время: at 5 o\'clock.\n'
        '• on — дни/даты: on Monday.\n'
        '• in — месяцы/годы/периоды: in July, in 2020, in the morning.',
    ),
    (
        ('there is', 'there are', 'есть/имеется', 'there'),
        '📘 There is / There are — «есть/имеется».\n'
        '• There is + единственное: There is a book.\n'
        '• There are + множественное: There are two books.\n'
        'Вопрос: Is there…? Are there…?',
    ),
]


def explain(question: str) -> str | None:
    """Return a canned explanation if the question matches a known topic."""
    if not question:
        return None
    q = f' {question.lower()} '
    for keywords, text in _TOPICS:
        if any(kw in q for kw in keywords):
            return text
    return None
