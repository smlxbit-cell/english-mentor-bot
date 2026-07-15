"""Canonical grammar rules bank (A1–A2) for the Rules Library map.

Rules appear in episodes via grammar_note + rule_key; the full bank is seeded
here so the map is populated even before every episode is written.
"""

from __future__ import annotations

# topic → ordered rules. `order` sorts within level+topic in the map.
RULES_BANK: list[dict] = [
    # ── A1 · Приветствия ──────────────────────────────────────────────
    {
        'key': 'greetings-hello',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'Hello / Hi / Good morning',
        'order': 1,
        'summary_ru': 'Самые частые приветствия. Hi — неформально, Good morning — до полудня.',
        'table': {
            'headers': ['Ситуация', 'Фраза', 'Перевод'],
            'rows': [
                ['Нейтрально', 'Hello!', 'Здравствуй!'],
                ['Друзья', 'Hi!', 'Привет!'],
                ['Утро', 'Good morning!', 'Доброе утро!'],
                ['Вечер', 'Good evening!', 'Добрый вечер!'],
            ],
        },
        'examples': [
            {'en': 'Hi! Nice to meet you.', 'ru': 'Привет! Приятно познакомиться.'},
            {'en': 'Good morning! How are you?', 'ru': 'Доброе утро! Как дела?'},
        ],
        'tip_ru': 'На «How are you?» часто отвечают «Good, thanks!» — не нужен длинный ответ.',
    },
    {
        'key': 'greetings-goodbye',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'Goodbye / See you',
        'order': 2,
        'summary_ru': 'Прощания: от нейтрального до тёплого.',
        'table': {
            'headers': ['Фраза', 'Пример', 'Перевод'],
            'rows': [
                ['Goodbye', 'Goodbye! Have a nice day.', 'До свидания! Хорошего дня.'],
                ['Bye', 'Bye! See you tomorrow.', 'Пока! До завтра.'],
                ['See you', 'See you later!', 'Увидимся!'],
            ],
        },
        'examples': [
            {'en': 'Bye! Thanks for your help.', 'ru': 'Пока! Спасибо за помощь.'},
        ],
        'tip_ru': 'See you later = «увидимся позже» — очень разговорная форма.',
    },
    # ── A1 · Просьбы ──────────────────────────────────────────────────
    {
        'key': 'polite-requests',
        'level': 'a1',
        'topic': 'Вежливые слова и фразы',
        'title': 'Вежливые просьбы',
        'order': 1,
        'summary_ru': 'Вежливее «I would like…», чем «I want…». Please смягчает просьбу.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['I would like…', 'I would like a coffee.', 'Я бы хотел кофе.'],
                ['Can I have…?', 'Can I have a tea, please?', 'Можно мне чай?'],
                ['…, please', 'Water, please.', 'Воду, пожалуйста.'],
            ],
        },
        'examples': [
            {'en': 'I would like a latte, please.', 'ru': 'Я бы хотел латте, пожалуйста.'},
            {'en': 'Can I have the menu, please?', 'ru': 'Можно меню, пожалуйста?'},
        ],
        'tip_ru': '«I want coffee» звучит грубовато в кафе и на работе.',
    },
    {
        'key': 'thank-you-responses',
        'level': 'a1',
        'topic': 'Вежливые слова и фразы',
        'title': 'Thank you / You\'re welcome',
        'order': 2,
        'summary_ru': 'Благодарность и короткие ответы на неё.',
        'table': {
            'headers': ['Фраза', 'Пример', 'Перевод'],
            'rows': [
                ['Thank you', 'Thank you very much!', 'Большое спасибо!'],
                ['Thanks', 'Thanks for your help.', 'Спасибо за помощь.'],
                ["You're welcome", "You're welcome!", 'Пожалуйста! (на спасибо)'],
            ],
        },
        'examples': [
            {'en': 'Thanks a lot!', 'ru': 'Большое спасибо!'},
            {'en': "No problem!", 'ru': 'Без проблем! (ответ на спасибо)'},
        ],
        'tip_ru': 'No problem / Sure — современные ответы вместо You\'re welcome.',
    },
    # ── A1 · To be ────────────────────────────────────────────────────
    {
        'key': 'to-be-basics',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'I am / you are / he is',
        'order': 1,
        'summary_ru': 'To be = «быть». Не требует вспомогательного do в вопросах.',
        'table': {
            'headers': ['Лицо', 'Форма', 'Пример'],
            'rows': [
                ['I', 'am', 'I am from Russia.'],
                ['you / we / they', 'are', 'You are kind.'],
                ['he / she / it', 'is', 'She is a teacher.'],
            ],
        },
        'examples': [
            {'en': 'I am fine, thank you.', 'ru': 'У меня всё хорошо, спасибо.'},
            {'en': 'It is cold today.', 'ru': 'Сегодня холодно.'},
        ],
        'tip_ru': 'В разговорной речи: I\'m, you\'re, he\'s.',
    },
    # ── A1 · Артикли ──────────────────────────────────────────────────
    {
        'key': 'articles-a-an',
        'level': 'a1',
        'topic': 'Артикли',
        'title': 'Артикли a / an',
        'order': 1,
        'summary_ru': 'A перед согласным звуком, an перед гласным.',
        'table': {
            'headers': ['Артикль', 'Пример', 'Перевод'],
            'rows': [
                ['a', 'a cup of coffee', 'чашка кофе'],
                ['a', 'a hotel', 'отель'],
                ['an', 'an apple', 'яблоко'],
                ['an', 'an hour', 'час (h не читается!)'],
            ],
        },
        'examples': [
            {'en': 'I need a room.', 'ru': 'Мне нужен номер.'},
            {'en': 'It is an interesting city.', 'ru': 'Это интересный город.'},
        ],
        'tip_ru': 'Смотри на звук, не на букву: an hour, a university.',
    },
    # ── A1 · Существительные ──────────────────────────────────────────
    {
        'key': 'plural-s',
        'level': 'a1',
        'topic': 'Существительные',
        'title': 'Множественное число (+s)',
        'order': 1,
        'summary_ru': 'Большинство слов: просто +s в конце.',
        'table': {
            'headers': ['Единственное', 'Множественное', 'Пример'],
            'rows': [
                ['cup', 'cups', 'two cups of tea'],
                ['ticket', 'tickets', 'train tickets'],
                ['day', 'days', 'three days'],
            ],
        },
        'examples': [
            {'en': 'I have two tickets.', 'ru': 'У меня два билета.'},
        ],
        'tip_ru': 'После -s / -x / -ch / -sh: +es (boxes, watches).',
    },
    # ── A2 · Present Simple ───────────────────────────────────────────
    {
        'key': 'present-simple-affirmative',
        'level': 'a2',
        'topic': 'Present Simple',
        'title': 'Утверждения в Present Simple',
        'order': 1,
        'summary_ru': 'Привычки и факты. He/she/it → глагол +s.',
        'table': {
            'headers': ['Лицо', 'Форма', 'Пример'],
            'rows': [
                ['I / you / we / they', 'work', 'They work in London.'],
                ['he / she / it', 'works', 'She works in IT.'],
                ['I / you / we / they', 'live', 'We live near the centre.'],
            ],
        },
        'examples': [
            {'en': 'He speaks English every day.', 'ru': 'Он говорит по-английски каждый день.'},
        ],
        'tip_ru': 'Маркеры: every day, usually, often, always.',
    },
    {
        'key': 'present-simple-questions',
        'level': 'a2',
        'topic': 'Present Simple',
        'title': 'Вопросы в Present Simple',
        'order': 2,
        'summary_ru': 'Do/does в начале. С to be — без do.',
        'table': {
            'headers': ['Вопрос', 'Пример', 'Перевод'],
            'rows': [
                ['Do you…?', 'Do you like coffee?', 'Ты любишь кофе?'],
                ['Does he…?', 'Does he work here?', 'Он здесь работает?'],
                ['Where are you from?', 'Where are you from?', 'Откуда ты?'],
            ],
        },
        'examples': [
            {'en': 'What do you do?', 'ru': 'Кем ты работаешь?'},
            {'en': 'Do you like tea?', 'ru': 'Ты любишь чай?'},
        ],
        'tip_ru': 'С to be вопрос без do: «Are you from Russia?»',
    },
    # ── A2 · Вопросы и знакомство ─────────────────────────────────────
    {
        'key': 'wh-questions-basics',
        'level': 'a2',
        'topic': 'Вопросы',
        'title': 'Wh-вопросы: what, where, who',
        'order': 1,
        'summary_ru': 'Wh-слово в начале + порядок как в вопросе.',
        'table': {
            'headers': ['Слово', 'Вопрос', 'Перевод'],
            'rows': [
                ['What', 'What is your name?', 'Как тебя зовут?'],
                ['Where', 'Where do you live?', 'Где ты живёшь?'],
                ['Who', 'Who is she?', 'Кто она?'],
            ],
        },
        'examples': [
            {'en': 'What do you do for work?', 'ru': 'Кем ты работаешь?'},
        ],
        'tip_ru': 'What do you do? = «чем занимаешься?» (про работу).',
    },
    # ── A2 · Навигация ────────────────────────────────────────────────
    {
        'key': 'navigation-where',
        'level': 'a2',
        'topic': 'Навигация',
        'title': 'Где? Как пройти?',
        'order': 1,
        'summary_ru': 'Спросить дорогу и понять ответ — must-have в городе.',
        'table': {
            'headers': ['Фраза', 'Пример', 'Перевод'],
            'rows': [
                ['Where is…?', 'Where is the station?', 'Где вокзал?'],
                ['How do I get to…?', 'How do I get to the hotel?', 'Как добраться до отеля?'],
                ['Is it far?', 'Is it far from here?', 'Это далеко отсюда?'],
            ],
        },
        'examples': [
            {'en': 'Excuse me, where is the toilet?', 'ru': 'Извините, где туалет?'},
            {'en': 'Go straight and turn left.', 'ru': 'Идите прямо и поверните налево.'},
        ],
        'tip_ru': 'Excuse me — вежливо привлечь внимание прохожего.',
    },
    {
        'key': 'navigation-directions',
        'level': 'a2',
        'topic': 'Навигация',
        'title': 'Указания: left, right, straight',
        'order': 2,
        'summary_ru': 'Понимать и давать простые указания.',
        'table': {
            'headers': ['Слово', 'Пример', 'Перевод'],
            'rows': [
                ['left', 'Turn left at the corner.', 'Поверни налево на углу.'],
                ['right', 'It is on the right.', 'Это справа.'],
                ['straight', 'Go straight ahead.', 'Идите прямо.'],
                ['near', 'It is near the park.', 'Это рядом с парком.'],
            ],
        },
        'examples': [
            {'en': 'The café is next to the bank.', 'ru': 'Кафе рядом с банком.'},
        ],
        'tip_ru': 'Next to = рядом с, opposite = напротив.',
    },
    # ── A2 · Предлоги ─────────────────────────────────────────────────
    {
        'key': 'prepositions-place',
        'level': 'a2',
        'topic': 'Предлоги',
        'title': 'In / on / at (место)',
        'order': 1,
        'summary_ru': 'In — внутри, on — на поверхности, at — точка/место.',
        'table': {
            'headers': ['Предлог', 'Пример', 'Перевод'],
            'rows': [
                ['in', 'in London / in the room', 'в Лондоне / в комнате'],
                ['on', 'on the table / on Main Street', 'на столе / на ул. Main'],
                ['at', 'at the airport / at work', 'в аэропорту / на работе'],
            ],
        },
        'examples': [
            {'en': 'I am at the hotel.', 'ru': 'Я в отеле.'},
            {'en': 'She is in Manchester.', 'ru': 'Она в Манчестере.'},
        ],
        'tip_ru': 'At the station — at для «точек» без границ.',
    },
    # ── A2 · Модальные ────────────────────────────────────────────────
    {
        'key': 'modal-can',
        'level': 'a2',
        'topic': 'Модальные глаголы',
        'title': 'Can — умение и просьба',
        'order': 1,
        'summary_ru': 'Can + глагол без to: умения и вежливые просьбы.',
        'table': {
            'headers': ['Значение', 'Пример', 'Перевод'],
            'rows': [
                ['Умение', 'I can swim.', 'Я умею плавать.'],
                ['Просьба', 'Can you help me?', 'Можешь помочь?'],
                ['Разрешение', 'Can I sit here?', 'Можно сесть здесь?'],
            ],
        },
        'examples': [
            {'en': 'Can you speak slower, please?', 'ru': 'Можешь говорить медленнее?'},
        ],
        'tip_ru': 'Could you…? — чуть вежливее, чем Can you…?',
    },
    {
        'key': 'modal-could-polite',
        'level': 'a2',
        'topic': 'Модальные глаголы',
        'title': 'Could — вежливые просьбы',
        'order': 2,
        'summary_ru': 'Could звучит мягче Can в просьбах к незнакомым.',
        'table': {
            'headers': ['Фраза', 'Пример', 'Перевод'],
            'rows': [
                ['Could you…?', 'Could you repeat that?', 'Не могли бы повторить?'],
                ['Could I…?', 'Could I have a receipt?', 'Можно чек?'],
            ],
        },
        'examples': [
            {'en': 'Could you tell me the way?', 'ru': 'Не подскажете дорогу?'},
        ],
        'tip_ru': 'На Could I…? часто отвечают «Of course!» / «Sure!»',
    },
    # ── A2 · Отель ────────────────────────────────────────────────────
    {
        'key': 'hotel-check-in',
        'level': 'a2',
        'topic': 'Отель',
        'title': 'Заселение в отель',
        'order': 1,
        'summary_ru': 'На ресепшене: представься, назови бронь, подтверди детали.',
        'table': {
            'headers': ['Ситуация', 'Фраза', 'Перевод'],
            'rows': [
                ['Заселение', "I'd like to check in, please.", 'Я бы хотел заселиться.'],
                ['Бронь', 'I have a reservation under Smith.', 'У меня бронь на имя Смит.'],
                ['Паспорт', 'Here is my passport.', 'Вот мой паспорт.'],
                ['Номер', 'Could I have the key, please?', 'Можно ключ?'],
            ],
        },
        'examples': [
            {'en': 'I have a reservation for two nights.', 'ru': 'У меня бронь на две ночи.'},
            {'en': 'What time is breakfast?', 'ru': 'Во сколько завтрак?'},
        ],
        'tip_ru': 'Under Smith = «на имя Смит» (фамилия в брони).',
    },
    # ── A2 · Работа ───────────────────────────────────────────────────
    {
        'key': 'work-small-talk',
        'level': 'a2',
        'topic': 'Работа',
        'title': 'О работе: small talk',
        'order': 1,
        'summary_ru': 'Present Simple: I work… / I am a… — коротко о роли и команде.',
        'table': {
            'headers': ['Вопрос', 'Ответ', 'Перевод'],
            'rows': [
                ['What do you do?', 'I work in e-commerce.', 'Я в e-commerce.'],
                ['What is your role?', 'I am on the product team.', 'Я в продуктовой команде.'],
                ['Nice to meet you', 'Nice to meet you too!', 'Мне тоже приятно!'],
            ],
        },
        'examples': [
            {'en': 'I work with online stores.', 'ru': 'Я работаю с онлайн-магазинами.'},
            {'en': 'My team handles product listings.', 'ru': 'Команда ведёт карточки товаров.'},
        ],
        'tip_ru': 'На первом рабочем дне достаточно 1–2 фраз — не нужен длинный рассказ.',
    },
    # ── B1 · Работа ───────────────────────────────────────────────────
    {
        'key': 'work-updates',
        'level': 'b1',
        'topic': 'Работа',
        'title': 'Короткий рабочий update',
        'order': 1,
        'summary_ru': 'Шаблон стендапа: что сделано → что дальше → блокеры.',
        'table': {
            'headers': ['Блок', 'Фраза', 'Перевод'],
            'rows': [
                ['Сделано', 'Yesterday I finished the draft.', 'Вчера закончил черновик.'],
                ['Дальше', 'Today I will run QA.', 'Сегодня сделаю QA.'],
                ['Блокеры', 'No blockers for now.', 'Пока без блокеров.'],
            ],
        },
        'examples': [
            {'en': 'Quick update: listings done. Next: analytics.', 'ru': 'Кратко: листинги готовы. Дальше: аналитика.'},
            {'en': 'One blocker: waiting for design.', 'ru': 'Блокер: жду дизайн.'},
        ],
        'tip_ru': 'В Slack/Teams три коротких предложения часто лучше абзаца.',
    },
    # ── B1 · Present Perfect / Conditionals ───────────────────────────
    {
        'key': 'present-perfect-since-for',
        'level': 'b1',
        'topic': 'Present Perfect',
        'title': 'Since / For',
        'order': 1,
        'summary_ru': 'Present Perfect: since = точка начала, for = длительность.',
        'table': {
            'headers': ['Слово', 'Пример', 'Перевод'],
            'rows': [
                ['since', "I've lived here since 2010.", 'Я живу здесь с 2010.'],
                ['for', "I've lived here for 5 years.", 'Я живу здесь 5 лет.'],
                ['already', 'She has already finished.', 'Она уже закончила.'],
            ],
        },
        'examples': [
            {'en': "I've known her since university.", 'ru': 'Я знаю её с университета.'},
            {'en': 'We have worked together for two years.', 'ru': 'Мы работаем вместе два года.'},
        ],
        'tip_ru': 'Since + дата/момент. For + период (for a week / for years).',
    },
    {
        'key': 'second-conditional',
        'level': 'b1',
        'topic': 'Условие',
        'title': 'Второе условное (If I had…)',
        'order': 1,
        'summary_ru': 'Нереальное сейчас: If + Past Simple, would + глагол.',
        'table': {
            'headers': ['Часть', 'Пример', 'Перевод'],
            'rows': [
                ['If…', 'If I had more time,', 'Если бы у меня было больше времени,'],
                ['…would', 'I would travel more.', 'я бы больше путешествовал.'],
                ['Wish', 'I wish I spoke English fluently.', 'Хотел бы говорить свободно.'],
            ],
        },
        'examples': [
            {'en': 'If I knew, I would tell you.', 'ru': 'Если бы я знал, я бы сказал.'},
        ],
        'tip_ru': 'С I после if — was или were: If I were you… (формальная норма).',
    },
    {
        'key': 'suggest-gerund',
        'level': 'b2',
        'topic': 'Герундий',
        'title': 'Suggest + -ing',
        'order': 1,
        'summary_ru': 'После suggest обычно герундий: suggested leaving.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['suggest + -ing', 'She suggested leaving earlier.', 'Она предложила уйти раньше.'],
                ['look forward to + -ing', 'I look forward to seeing you.', 'Жду встречи.'],
            ],
        },
        'examples': [
            {'en': 'He suggested taking a taxi.', 'ru': 'Он предложил взять такси.'},
        ],
        'tip_ru': 'Не «suggested leave» — нужна форма -ing.',
    },
]
