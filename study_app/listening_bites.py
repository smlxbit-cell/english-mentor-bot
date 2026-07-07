"""Short listening comprehension bites for daily plans (level-tagged)."""

from __future__ import annotations

import hashlib
from datetime import date

LISTENING_BITES: list[dict] = [
    {
        'level': 'a1',
        'title': 'At the café',
        'lines': [
            {'en': 'Hi! What can I get for you?', 'ru': 'Здравствуйте! Что для вас?'},
            {'en': 'I would like a cappuccino, please.', 'ru': 'Я бы хотел капучино, пожалуйста.'},
            {'en': 'Sure. Anything else?', 'ru': 'Конечно. Ещё что-нибудь?'},
            {'en': 'No, thank you.', 'ru': 'Нет, спасибо.'},
        ],
        'question_ru': 'Что заказал клиент?',
        'options': ['A cappuccino', 'A sandwich', 'A tea', 'Water'],
        'correct_index': 0,
        'minutes': 4,
    },
    {
        'level': 'a2',
        'title': 'Meeting a friend',
        'lines': [
            {'en': 'Hey! How are you?', 'ru': 'Привет! Как дела?'},
            {'en': 'Good, thanks! And you?', 'ru': 'Хорошо, спасибо! А у тебя?'},
            {'en': 'Not bad. Busy week at work.', 'ru': 'Неплохо. Напряжённая неделя на работе.'},
        ],
        'question_ru': 'Как у собеседника дела на работе?',
        'options': ['Busy week', 'On holiday', 'Looking for a job', 'Sick leave'],
        'correct_index': 0,
        'minutes': 4,
    },
    {
        'level': 'a2',
        'title': 'At the hotel',
        'lines': [
            {'en': 'Good evening. I have a reservation.', 'ru': 'Добрый вечер. У меня бронь.'},
            {'en': 'Welcome! Your name, please?', 'ru': 'Добро пожаловать! Ваше имя?'},
            {'en': 'Emma Clarke.', 'ru': 'Эмма Кларк.'},
            {'en': 'Room 204. Here is your key.', 'ru': 'Номер 204. Вот ваш ключ.'},
        ],
        'question_ru': 'Какой номер комнаты?',
        'options': ['204', '402', '240', '420'],
        'correct_index': 0,
        'minutes': 4,
    },
    {
        'level': 'b1',
        'title': 'Office stand-up',
        'lines': [
            {'en': 'Quick update from my side.', 'ru': 'Короткий апдейт с моей стороны.'},
            {'en': 'Yesterday I finished the product page.', 'ru': 'Вчера закончил страницу товара.'},
            {'en': 'Today I will check analytics. No blockers.', 'ru': 'Сегодня проверю аналитику. Блокеров нет.'},
        ],
        'question_ru': 'Что планируется сегодня?',
        'options': ['Check analytics', 'Book a hotel', 'Write a novel', 'Take a flight'],
        'correct_index': 0,
        'minutes': 4,
    },
    {
        'level': 'b2',
        'title': 'Team call',
        'lines': [
            {'en': 'Despite the tight deadline, we are on track.', 'ru': 'Несмотря на жёсткий дедлайн, мы по плану.'},
            {'en': 'The client asked for a revised summary by Thursday.', 'ru': 'Клиент просил обновлённое резюме к четвергу.'},
            {'en': 'I will draft it after the stand-up.', 'ru': 'Я подготовлю черновик после стендапа.'},
        ],
        'question_ru': 'Что нужно сделать после стендапа?',
        'options': ['Draft a revised summary', 'Cancel the project', 'Take a vacation', 'Order lunch'],
        'correct_index': 0,
        'minutes': 4,
    },
]

LEVEL_ORDER = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']


def _level_index(level: str) -> int:
    lv = (level or 'a2').lower()
    try:
        return LEVEL_ORDER.index(lv)
    except ValueError:
        return 1


def pick_listening_bite(user_id: int, day: date, *, user_level: str = 'a2') -> dict:
    user_idx = _level_index(user_level)
    pool = [
        b for b in LISTENING_BITES
        if _level_index(b.get('level', 'a2')) <= user_idx
    ] or LISTENING_BITES
    raw = f'{user_id}:{day.isoformat()}:listen'.encode()
    idx = int(hashlib.sha256(raw).hexdigest(), 16) % len(pool)
    return pool[idx]
