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
    {
        'key': 'sorry-excuse-me',
        'level': 'a1',
        'topic': 'Вежливые слова и фразы',
        'title': 'Sorry / Excuse me',
        'order': 3,
        'summary_ru': 'Sorry — извинение. Excuse me — привлечь внимание или пройти.',
        'table': {
            'headers': ['Фраза', 'Пример', 'Перевод'],
            'rows': [
                ['Sorry', 'Sorry! I\'m late.', 'Извини! Я опоздал.'],
                ['Excuse me', 'Excuse me, where is the bank?', 'Извините, где банк?'],
                ['Pardon?', 'Pardon? I didn\'t hear you.', 'Простите? Я не расслышал.'],
            ],
        },
        'examples': [
            {'en': 'Sorry, I don\'t understand.', 'ru': 'Извини, я не понимаю.'},
        ],
        'tip_ru': 'Excuse me — не всегда «извини»: часто «извините, можно…?»',
    },
    {
        'key': 'yes-no-ok',
        'level': 'a1',
        'topic': 'Вежливые слова и фразы',
        'title': 'Yes / No / OK / Sure',
        'order': 4,
        'summary_ru': 'Короткие ответы в разговоре: yes, no, ok, sure.',
        'table': {
            'headers': ['Слово', 'Пример', 'Перевод'],
            'rows': [
                ['Yes', 'Yes, please.', 'Да, пожалуйста.'],
                ['No', 'No, thanks.', 'Нет, спасибо.'],
                ['OK / Sure', 'Sure! No problem.', 'Конечно! Без проблем.'],
            ],
        },
        'examples': [
            {'en': 'OK, let\'s go.', 'ru': 'Ок, пойдём.'},
        ],
        'tip_ru': 'Sure = «конечно» — дружелюбнее, чем просто yes.',
    },
    {
        'key': 'introducing-yourself',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'My name is… / Nice to meet you',
        'order': 3,
        'summary_ru': 'Представление: имя, страна, приятно познакомиться.',
        'table': {
            'headers': ['Фраза', 'Пример', 'Перевод'],
            'rows': [
                ['My name is…', 'My name is Anna.', 'Меня зовут Анна.'],
                ["I'm…", "I'm from Russia.", 'Я из России.'],
                ['Nice to meet you', 'Nice to meet you!', 'Приятно познакомиться!'],
            ],
        },
        'examples': [
            {'en': "I'm Alex. Nice to meet you!", 'ru': 'Я Алекс. Приятно познакомиться!'},
        ],
        'tip_ru': 'I\'m = I am — в разговоре почти всегда сокращают.',
    },
    {
        'key': 'numbers-1-20',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'Numbers 1–20',
        'order': 4,
        'summary_ru': 'Числа 1–20 — база для возраста, цены, времени.',
        'table': {
            'headers': ['Число', 'Слово', 'Пример'],
            'rows': [
                ['1–5', 'one, two, three, four, five', 'I have two cats. · У меня две кошки.'],
                ['6–10', 'six, seven, eight, nine, ten', 'Ten minutes. · Десять минут.'],
                ['11–20', 'eleven… twenty', 'I am fifteen. · Мне пятнадцать.'],
            ],
        },
        'examples': [
            {'en': 'Three apples, please.', 'ru': 'Три яблока, пожалуйста.'},
        ],
        'tip_ru': '13–19: fourteen, fifteen… (не «fourty» — forty только 40).',
    },
    {
        'key': 'numbers-21-100',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': '21–100 · How many?',
        'order': 5,
        'summary_ru': 'Десятки и «сколько?»: twenty, thirty… · How many?',
        'table': {
            'headers': ['Число', 'Слово', 'Пример'],
            'rows': [
                ['21–29', 'twenty-one… twenty-nine', 'I am twenty-five. · Мне 25.'],
                ['30–90', 'thirty, forty, fifty… ninety', 'She is thirty. · Ей 30.'],
                ['100', 'a hundred', 'How many? — Ten. · Сколько? — Десять.'],
            ],
        },
        'examples': [
            {'en': 'There are fifty people.', 'ru': 'Здесь пятьдесят человек.'},
        ],
        'tip_ru': 'How many + исчисляемое (many apples). How much + неисчисляемое.',
    },
    {
        'key': 'time-oclock',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'What time is it? · o\'clock',
        'order': 6,
        'summary_ru': 'Время: What time is it? · It\'s three o\'clock.',
        'table': {
            'headers': ['Вопрос', 'Ответ', 'Перевод'],
            'rows': [
                ['What time is it?', 'It\'s one o\'clock.', 'Сейчас час.'],
                ['What time is it?', 'It\'s half past two.', 'Сейчас половина третьего.'],
                ['What time is it?', 'It\'s a quarter past four.', 'Сейчас четверть пятого.'],
            ],
        },
        'examples': [
            {'en': 'It\'s five o\'clock.', 'ru': 'Сейчас пять часов.'},
        ],
        'tip_ru': 'o\'clock = ровно час · half past = 30 мин · quarter past = 15 мин.',
    },
    {
        'key': 'days-months',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'Days / Months · Monday… January…',
        'order': 7,
        'summary_ru': 'Дни недели и месяцы: on Monday · in January.',
        'table': {
            'headers': ['Слово', 'Пример', 'Перевод'],
            'rows': [
                ['Monday', 'Today is Monday.', 'Сегодня понедельник.'],
                ['on Friday', 'See you on Friday.', 'Увидимся в пятницу.'],
                ['in January', 'My birthday is in January.', 'Мой день рождения в январе.'],
            ],
        },
        'examples': [
            {'en': 'The meeting is on Tuesday.', 'ru': 'Встреча во вторник.'},
        ],
        'tip_ru': 'on + день недели · in + месяц (in July, on Sunday).',
    },
    {
        'key': 'cafe-order-basic',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'A coffee, please',
        'order': 8,
        'summary_ru': 'Заказ в кафе: коротко и вежливо с please.',
        'table': {
            'headers': ['Фраза', 'Пример', 'Перевод'],
            'rows': [
                ['A coffee, please', 'A coffee, please.', 'Кофе, пожалуйста.'],
                ['Can I have…?', 'Can I have a latte, please?', 'Можно латте, пожалуйста?'],
                ['For here / to go', 'For here, please.', 'Здесь, пожалуйста.'],
            ],
        },
        'examples': [
            {'en': 'Two teas, please.', 'ru': 'Два чая, пожалуйста.'},
        ],
        'tip_ru': 'For here = здесь · to go = с собой (takeout).',
    },
    {
        'key': 'how-are-you',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'How are you? · Fine, thanks',
        'order': 9,
        'summary_ru': '«Как дела?» — короткий ответ лучше длинного.',
        'table': {
            'headers': ['Вопрос', 'Ответ', 'Перевод'],
            'rows': [
                ['How are you?', 'I\'m fine, thanks.', 'Нормально, спасибо.'],
                ['How are you?', 'Good, thanks. And you?', 'Хорошо, спасибо. А ты?'],
                ['How are you doing?', 'Not bad, thanks.', 'Неплохо, спасибо.'],
            ],
        },
        'examples': [
            {'en': 'I\'m OK, thanks.', 'ru': 'Нормально, спасибо.'},
        ],
        'tip_ru': 'Fine / Good / OK — короткий ответ. Не нужно длинное «рассказ о жизни».',
    },
    {
        'key': 'good-night',
        'level': 'a1',
        'topic': 'Приветствия',
        'title': 'Good night / Sleep well',
        'order': 10,
        'summary_ru': 'Перед сном: Good night · Sleep well · Sweet dreams.',
        'table': {
            'headers': ['Фраза', 'Пример', 'Перевод'],
            'rows': [
                ['Good night', 'Good night! See you tomorrow.', 'Спокойной ночи! До завтра.'],
                ['Sleep well', 'Sleep well!', 'Спи хорошо!'],
                ['Sweet dreams', 'Sweet dreams!', 'Сладких снов!'],
            ],
        },
        'examples': [
            {'en': 'Good night, Mom!', 'ru': 'Спокойной ночи, мама!'},
        ],
        'tip_ru': 'Good night — когда уходишь спать. Good evening — вечером, но ещё не спишь.',
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
            'headers': ['Лицо', 'Пример', 'Перевод'],
            'rows': [
                ['I · am', 'I am from Russia.', 'Я из России.'],
                ['you · are', 'You are kind.', 'Ты добрый.'],
                ['he/she · is', 'She is a teacher.', 'Она учитель.'],
            ],
        },
        'examples': [
            {'en': 'I am fine, thank you.', 'ru': 'У меня всё хорошо, спасибо.'},
            {'en': 'It is cold today.', 'ru': 'Сегодня холодно.'},
        ],
        'tip_ru': 'В разговорной речи: I\'m, you\'re, he\'s.',
    },
    {
        'key': 'to-be-negative',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'I am not / isn\'t / aren\'t',
        'order': 2,
        'summary_ru': 'Отрицание с to be: am not / isn\'t / aren\'t — без do.',
        'table': {
            'headers': ['Лицо', 'Пример', 'Перевод'],
            'rows': [
                ['I · am not', 'I am not tired.', 'Я не устал.'],
                ['he/she · isn\'t', 'She isn\'t ready.', 'Она не готова.'],
                ['you/we · aren\'t', 'You aren\'t late.', 'Ты не опоздал.'],
            ],
        },
        'examples': [
            {'en': 'It isn\'t cold today.', 'ru': 'Сегодня не холодно.'},
        ],
        'tip_ru': 'Сокращения: I\'m not · he\'s not / he isn\'t',
    },
    {
        'key': 'to-be-questions',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'Am I…? / Are you…? / Is he…?',
        'order': 3,
        'summary_ru': 'Вопрос с to be: форма am/is/are **в начале** — без do.',
        'table': {
            'headers': ['Вопрос', 'Пример', 'Перевод'],
            'rows': [
                ['Am I…?', 'Am I late?', 'Я опаздываю?'],
                ['Are you…?', 'Are you ready?', 'Ты готов?'],
                ['Is he/she…?', 'Is she at home?', 'Она дома?'],
            ],
        },
        'examples': [
            {'en': 'Are they students?', 'ru': 'Они студенты?'},
        ],
        'tip_ru': 'To be: вопрос = форма to be в начале (без do).',
    },
    {
        'key': 'to-be-short-forms',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'I\'m / you\'re / he\'s',
        'order': 4,
        'summary_ru': 'В разговорной речи to be почти всегда сокращают.',
        'table': {
            'headers': ['Полная', 'Краткая', 'Пример'],
            'rows': [
                ['I am', 'I\'m', 'I\'m fine. · У меня всё хорошо.'],
                ['you are', 'you\'re', 'You\'re welcome. · Пожалуйста.'],
                ['he is', 'he\'s', 'He\'s a doctor. · Он врач.'],
            ],
        },
        'examples': [
            {'en': 'She\'s at home.', 'ru': 'Она дома.'},
        ],
        'tip_ru': 'I\'m = I am · you\'re = you are · he\'s = he is',
    },
    {
        'key': 'there-is-are-affirm',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'There is / There are',
        'order': 5,
        'summary_ru': 'There is + единственное · There are + множественное — «есть / имеется».',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['There is', 'There is a shop here.', 'Здесь есть магазин.'],
                ['There is', 'There is a problem.', 'Есть проблема.'],
                ['There are', 'There are two parks.', 'Здесь два парка.'],
            ],
        },
        'examples': [
            {'en': 'There are many people.', 'ru': 'Здесь много людей.'},
        ],
        'tip_ru': 'There is → There\'s · a/an после there is',
    },
    {
        'key': 'there-is-are-questions',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'Is there…? / Are there…?',
        'order': 6,
        'summary_ru': 'Вопрос с there: Is there…? / Are there…? — порядок как в утверждении.',
        'table': {
            'headers': ['Вопрос', 'Пример', 'Перевод'],
            'rows': [
                ['Is there…?', 'Is there a bank near here?', 'Здесь рядом есть банк?'],
                ['Is there…?', 'Is there any milk?', 'Есть молоко?'],
                ['Are there…?', 'Are there any seats?', 'Есть свободные места?'],
            ],
        },
        'examples': [
            {'en': 'Are there many tourists?', 'ru': 'Здесь много туристов?'},
        ],
        'tip_ru': 'Краткий ответ: Yes, there is. / No, there aren\'t.',
    },
    {
        'key': 'have-got-affirm',
        'level': 'a1',
        'topic': 'Глагол have',
        'title': 'I have / She has',
        'order': 7,
        'summary_ru': 'Have = «иметь, у меня есть». В US English: I have, she has.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['I have', 'I have a dog.', 'У меня есть собака.'],
                ['You have', 'You have time.', 'У тебя есть время.'],
                ['She has', 'She has blue eyes.', 'У неё голубые глаза.'],
            ],
        },
        'examples': [
            {'en': 'We have a new car.', 'ru': 'У нас новая машина.'},
        ],
        'tip_ru': '🇬🇧 British: I\'ve got / she\'s got — то же значение, часто в UK.',
    },
    {
        'key': 'have-got-questions',
        'level': 'a1',
        'topic': 'Глагол have',
        'title': 'Do you have…? / Does she have…?',
        'order': 8,
        'summary_ru': 'Do you have…? = «У тебя есть…?» · Does she have…?',
        'table': {
            'headers': ['Вопрос', 'Пример', 'Перевод'],
            'rows': [
                ['Do you have…?', 'Do you have a pen?', 'У тебя есть ручка?'],
                ['Do you have…?', 'Do you have any money?', 'У тебя есть деньги?'],
                ['Does she have…?', 'Does she have a car?', 'У неё есть машина?'],
            ],
        },
        'examples': [
            {'en': 'Do they have children?', 'ru': 'У них есть дети?'},
        ],
        'tip_ru': '🇬🇧 British: Have you got…? / Has she got…? · Ответ US: Yes, I do. / No, I don\'t.',
    },
    {
        'key': 'imperatives-affirm',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'Open… / Sit down / Listen',
        'order': 9,
        'summary_ru': 'Повелительное наклонение: глагол без подлежащего. Please смягчает.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['Open…', 'Open the door, please.', 'Открой дверь, пожалуйста.'],
                ['Sit down', 'Sit down.', 'Садись.'],
                ['Listen', 'Listen to me.', 'Послушай меня.'],
            ],
        },
        'examples': [
            {'en': 'Please wait here.', 'ru': 'Подожди здесь, пожалуйста.'},
        ],
        'tip_ru': 'Please в начале или конце — вежливее.',
    },
    {
        'key': 'imperatives-negative',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'Don\'t… / Don\'t worry',
        'order': 10,
        'summary_ru': 'Отрицательный приказ: don\'t + глагол. Тон дружелюбный, не грубый.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['Don\'t…', 'Don\'t run!', 'Не бегай!'],
                ['Don\'t…', 'Don\'t worry.', 'Не волнуйся.'],
                ['Don\'t open…', 'Don\'t open the window.', 'Не открывай окно.'],
            ],
        },
        'examples': [
            {'en': 'Don\'t be late.', 'ru': 'Не опаздывай.'},
        ],
        'tip_ru': 'Don\'t = Do not. Please смягчает и в отрицании.',
    },
    {
        'key': 'can-ability',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'I can / She can',
        'order': 11,
        'summary_ru': 'Can = «уметь, мочь». После can — глагол без to.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['I can', 'I can swim.', 'Я умею плавать.'],
                ['She can', 'She can speak English.', 'Она говорит по-английски.'],
                ['We can', 'We can help.', 'Мы можем помочь.'],
            ],
        },
        'examples': [
            {'en': 'He can drive.', 'ru': 'Он умеет водить.'},
        ],
        'tip_ru': 'Can + глагол без to: I can swim (не to swim).',
    },
    {
        'key': 'can-permission',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'Can I…? / Can you…?',
        'order': 12,
        'summary_ru': 'Can I…? = вежливая просьба о разрешении. Can you…? = «можешь…?»',
        'table': {
            'headers': ['Вопрос', 'Пример', 'Перевод'],
            'rows': [
                ['Can I…?', 'Can I sit here?', 'Можно мне сесть здесь?'],
                ['Can we…?', 'Can we go now?', 'Можем идти?'],
                ['Can you…?', 'Can you help me?', 'Можешь помочь?'],
            ],
        },
        'examples': [
            {'en': 'Can I use your phone?', 'ru': 'Можно воспользоваться твоим телефоном?'},
        ],
        'tip_ru': 'Can I…? = May I…? (формальнее). Ответ: Sure! / Of course.',
    },
    {
        'key': 'can-negative',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'I can\'t / She can\'t',
        'order': 13,
        'summary_ru': 'Can\'t = cannot = «не могу / не умею». После can\'t — глагол без to.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['I can\'t', 'I can\'t swim.', 'Я не умею плавать.'],
                ['She can\'t', 'She can\'t come today.', 'Она не может прийти сегодня.'],
                ['We can\'t', 'We can\'t wait.', 'Мы не можем ждать.'],
            ],
        },
        'examples': [
            {'en': 'Sorry, I can\'t help.', 'ru': 'Извини, я не могу помочь.'},
        ],
        'tip_ru': 'Can\'t = cannot. Can\'t + глагол без to.',
    },
    {
        'key': 'present-simple-i-you',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'I work / You live',
        'order': 14,
        'summary_ru': 'Present Simple: факты и привычки. I/you/we/they — глагол без -s.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['I work', 'I work in an office.', 'Я работаю в офисе.'],
                ['You live', 'You live here.', 'Ты живёшь здесь.'],
                ['We study', 'We study English.', 'Мы учим английский.'],
            ],
        },
        'examples': [
            {'en': 'They play football.', 'ru': 'Они играют в футбол.'},
        ],
        'tip_ru': 'I / you / we / they — глагол без -s: I work (не works).',
    },
    {
        'key': 'present-simple-he-s',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'He works / She lives',
        'order': 15,
        'summary_ru': 'He/she/it — глагол с -s: works, lives, plays.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['He works', 'He works every day.', 'Он работает каждый день.'],
                ['She lives', 'She lives in London.', 'Она живёт в Лондоне.'],
                ['It rains', 'It rains a lot.', 'Здесь часто идёт дождь.'],
            ],
        },
        'examples': [
            {'en': 'My brother plays guitar.', 'ru': 'Мой брат играет на гитаре.'},
        ],
        'tip_ru': 'he / she / it → +s: work → works, live → lives.',
    },
    {
        'key': 'like-love-ing',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'I like reading',
        'order': 16,
        'summary_ru': 'Like / love + -ing: нравится заниматься чем-то.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['I like…', 'I like reading.', 'Мне нравится читать.'],
                ['She likes…', 'She likes music.', 'Ей нравится музыка.'],
                ['We love…', 'We love swimming.', 'Мы любим плавать.'],
            ],
        },
        'examples': [
            {'en': 'He likes pizza.', 'ru': 'Ему нравится пицца.'},
        ],
        'tip_ru': 'like/love + -ing. She likes → +s у like.',
    },
    {
        'key': 'want-would-like',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'I want / I\'d like',
        'order': 17,
        'summary_ru': 'Want = «хочу». I\'d like = вежливее, часто в кафе и просьбах.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['I want', 'I want water.', 'Я хочу воды.'],
                ['I\'d like', 'I\'d like a coffee, please.', 'Я бы хотел(а) кофе, пожалуйста.'],
                ['She wants', 'She wants to go.', 'Она хочет пойти.'],
            ],
        },
        'examples': [
            {'en': 'We\'d like two tickets.', 'ru': 'Мы бы хотели два билета.'},
        ],
        'tip_ru': 'I\'d like = I would like — вежливее, чем I want.',
    },
    {
        'key': 'lets',
        'level': 'a1',
        'topic': 'Глагол to be',
        'title': 'Let\'s go / Let\'s start',
        'order': 18,
        'summary_ru': 'Let\'s = Let us — предложение сделать что-то вместе.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['Let\'s go', 'Let\'s go!', 'Пойдём!'],
                ['Let\'s start', 'Let\'s start the lesson.', 'Давай начнём урок.'],
                ['Let\'s try', 'Let\'s try again.', 'Давай попробуем ещё раз.'],
            ],
        },
        'examples': [
            {'en': 'Let\'s eat.', 'ru': 'Давай поедим.'},
        ],
        'tip_ru': 'Let\'s = Let us. После let\'s — глагол без to.',
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
            'headers': ['Единственное', 'Множественное', 'Пример · перевод'],
            'rows': [
                ['cup', 'cups', 'two cups of tea · две чашки чая'],
                ['ticket', 'tickets', 'train tickets · билеты на поезд'],
                ['day', 'days', 'three days · три дня'],
            ],
        },
        'examples': [
            {'en': 'I have two tickets.', 'ru': 'У меня два билета.'},
        ],
        'tip_ru': 'После -s / -x / -ch / -sh: +es (boxes, watches).',
    },
    {
        'key': 'demonstratives-this-that',
        'level': 'a1',
        'topic': 'Указатели',
        'title': 'This / That — «этот» и «тот»',
        'order': 1,
        'summary_ru': 'This — близко (это здесь). That — дальше (то там).',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['this', 'This is my bag.', 'Это моя сумка (рядом).'],
                ['that', 'That is a bus.', 'Тот автобус (вдали).'],
                ['this + noun', 'This book is good.', 'Эта книга хорошая.'],
            ],
        },
        'examples': [
            {'en': 'Is this your phone?', 'ru': 'Это твой телефон?'},
            {'en': 'That shop is closed.', 'ru': 'Тот магазин закрыт.'},
        ],
        'tip_ru': 'These/those — множественное: these books, those people.',
    },
    {
        'key': 'possessives-my-your',
        'level': 'a1',
        'topic': 'Притяжательные',
        'title': 'My / Your / His / Her',
        'order': 1,
        'summary_ru': 'Притяжательные местоимения стоят перед существительным без артикля.',
        'table': {
            'headers': ['Форма', 'Пример', 'Перевод'],
            'rows': [
                ['my', 'my name', 'моё имя'],
                ['your', 'your room', 'твоя комната'],
                ['his / her', 'his job · her bag', 'его работа · её сумка'],
            ],
        },
        'examples': [
            {'en': 'What is your name?', 'ru': 'Как тебя зовут?'},
            {'en': 'This is my ticket.', 'ru': 'Это мой билет.'},
        ],
        'tip_ru': 'Its — «его/её» для предметов; its ≠ it\'s (it is).',
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
