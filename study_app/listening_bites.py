"""Short listening comprehension bites for 30+ minute daily plans."""

from __future__ import annotations

import hashlib
from datetime import date

LISTENING_BITES: list[dict] = [
    {
        'title': 'At the café',
        'lines': [
            {'en': 'Hi! What can I get for you?', 'ru': 'Здравствуйте! Что для вас?'},
            {'en': 'I would like a cappuccino, please.', 'ru': 'Я бы хотел капучино, пожалуйста.'},
            {'en': 'Sure. Anything else?', 'ru': 'Конечно. Ещё что-нибудь?'},
            {'en': 'No, thank you.', 'ru': 'Нет, спасибо.'},
        ],
        'question_ru': 'Что заказал клиент?',
        'options': [
            'A cappuccino',
            'A sandwich',
            'A tea',
            'Water',
        ],
        'correct_index': 0,
        'minutes': 4,
    },
    {
        'title': 'Meeting a friend',
        'lines': [
            {'en': 'Hey! How are you?', 'ru': 'Привет! Как дела?'},
            {'en': 'Good, thanks! And you?', 'ru': 'Хорошо, спасибо! А у тебя?'},
            {'en': 'Not bad. Busy week at work.', 'ru': 'Неплохо. Напряжённая неделя на работе.'},
        ],
        'question_ru': 'Как у собеседника дела на работе?',
        'options': [
            'Busy week',
            'On holiday',
            'Looking for a job',
            'Sick leave',
        ],
        'correct_index': 0,
        'minutes': 4,
    },
    {
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
]


def pick_listening_bite(user_id: int, day: date) -> dict:
    raw = f'{user_id}:{day.isoformat()}:listen'.encode()
    idx = int(hashlib.sha256(raw).hexdigest(), 16) % len(LISTENING_BITES)
    return LISTENING_BITES[idx]
