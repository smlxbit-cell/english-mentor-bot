"""Data-driven curriculum: units + lessons authored as data, not code.

Add new units/lessons by editing CURRICULUM below (or in the admin). `seed_curriculum`
is idempotent and rebuilds each lesson's steps from the data. This is the
"curated template" half of the hybrid model; AI personalization (see
ai_app.services.personalize) adds adaptive practice on top at runtime.
"""

from __future__ import annotations

from content_app.models import Character, Lesson, LessonStep, Unit

# --------------------------------------------------------------------------- #
# Lesson step data (English content is what gets voiced by TTS).
# --------------------------------------------------------------------------- #

_COFFEE_HINT_POLITE = (
    '📖 <b>Как заказать вежливо</b>\n\n'
    '▫️ <b>I would like</b> — «я бы хотел(а)». Мягче, чем <b>I want</b> («я хочу»).\n'
    '▫️ <b>a coffee</b> — артикль <b>a</b> перед одной порцией (a cup, a coffee).\n'
    '▫️ <b>please</b> в конце — вежливое «пожалуйста».\n\n'
    '🇬🇧 I would like a coffee, please.\n'
    '(Я бы хотел кофе, пожалуйста.)'
)

_COFFEE_STEPS = [
    {'type': 'hook',
     'content': {'scene_key': 'ep01_london'},
     'text': '☕️ <b>Эпизод 1. Coffee in London</b>\n\n'
             'Лондон, утро, лёгкий дождь. Ты только приехал — хочется кофе, '
             'но заговорить по-английски страшно.\n\n'
             'За соседним столиком девушка улыбается и машет рукой:\n'
             '🇬🇧 Hi! Are you new here?\n'
             '(Привет! Ты здесь новенький?)\n\n'
             'Это <b>Эмма</b> — она станет твоим гидом. Сегодня ты закажешь '
             'кофе как местный. Поехали!'},
    {'type': 'story', 'with_character': True,
     'content': {'scene_key': 'ep01_cafe'},
     'text': '📖 Эмма ведёт тебя в уютную кофейню на углу. Пахнет корицей и '
             'свежим кофе. За стойкой улыбается бариста <b>Том</b>.\n\n'
             'Эмма шепчёт:\n'
             '🇬🇧 Just be polite and smile — the rest is easy.\n'
             '(Будь вежлив и улыбайся — остальное просто.)\n\n'
             'Твоя очередь заказывать.'},
    {'type': 'vocabulary', 'skill': 'vocabulary',
     'content': {'words': [
         {'en': 'coffee', 'ru': 'кофе', 'example': 'I love coffee.',
          'example_ru': 'Я люблю кофе.'},
         {'en': 'tea', 'ru': 'чай', 'example': 'A cup of tea, please.',
          'example_ru': 'Чашку чая, пожалуйста.'},
         {'en': 'cup', 'ru': 'чашка', 'example': 'A cup of coffee.',
          'example_ru': 'Чашка кофе.'},
         {'en': 'please', 'ru': 'пожалуйста', 'example': 'Water, please.',
          'example_ru': 'Воды, пожалуйста.'},
         {'en': 'thank you', 'ru': 'спасибо', 'example': 'No, thank you.',
          'example_ru': 'Нет, спасибо.'},
         {'en': 'would like', 'ru': 'хотел(а) бы', 'example': 'I would like tea.',
          'example_ru': 'Я бы хотел чай.'},
     ]}},
    {'type': 'grammar_note', 'skill': 'grammar', 'title': 'Вежливые просьбы',
     'content': {
         'rule_ru': 'В английском вежливее сказать «I would like…» (Я бы хотел…), '
                    'чем «I want…» (Я хочу). А слово please в конце делает просьбу '
                    'мягкой и приятной.',
         'table': {
             'headers': ['Форма', 'Пример', 'Перевод'],
             'rows': [
                 ['I would like…', 'I would like a coffee.', 'Я бы хотел кофе.'],
                 ['Can I have…?', 'Can I have a tea, please?', 'Можно мне чай?'],
                 ['…, please', 'A cup of water, please.', 'Чашку воды, пожалуйста.'],
             ],
         },
         'examples': [
             {'en': 'I would like a latte, please.', 'ru': 'Я бы хотел латте, пожалуйста.'},
             {'en': 'Can I have the menu, please?', 'ru': 'Можно меню, пожалуйста?'},
         ],
         'tip_ru': 'Сравни: «I want coffee» звучит грубовато, «I would like a '
                   'coffee, please» — вежливо.',
         'rule_key': 'polite-requests',
     }},
    {'type': 'story',
     'text': '🗣️ <b>Готовая фраза для заказа:</b>\n\n'
             '🇬🇧 I would like a coffee, please.\n'
             '(Я бы хотел кофе, пожалуйста.)\n\n'
             'Запомни — сейчас попробуешь сам.',
     'content': {'speak_en': 'I would like a coffee, please.'}},
    {'type': 'exercise', 'skill': 'speaking',
     'text': '☕️ Том смотрит на тебя и спрашивает:\n'
             '🇬🇧 What can I get you?\n'
             '(Что для вас?)\n\n'
             'Как вежливо заказать кофе?\n'
             '<i>Не уверен? Нажми 💡 Подсказка</i>',
     'content': {'exercise_type': 'multiple_choice',
                 'options': ['Give me coffee.',
                             'I would like a coffee, please.',
                             'Coffee now.'],
                 'correct': ['I would like a coffee, please.'],
                 'rule_key': 'polite-requests',
                 'hint_detail_ru': _COFFEE_HINT_POLITE,
                 'explanation': '«I would like … , please» — вежливый заказ в кафе.'}},
    {'type': 'dialogue', 'skill': 'listening',
     'text': '💬 У стойки — послушай диалог:',
     'content': {'lines': [
         {'speaker': 'Tom', 'text': 'Good morning! What can I get you?',
          'ru': 'Доброе утро! Что для вас?'},
         {'speaker': 'Emma', 'text': 'I would like a tea, please.',
          'ru': 'Я бы хотел чай, пожалуйста.'},
         {'speaker': 'Tom', 'text': 'Of course. Anything else?',
          'ru': 'Конечно. Ещё что-нибудь?'},
         {'speaker': 'Emma', 'text': 'No, thank you.',
          'ru': 'Нет, спасибо.'},
     ]}},
    {'type': 'story',
     'text': '🌍 <b>Did you know?</b>\n\n'
             '🇬🇧 Britain drinks about 98 million cups of coffee a day.\n'
             '(В Британии выпивают около 98 миллионов чашек кофе в день.)\n\n'
             '🇬🇧 A café is a perfect place for your first polite phrases.\n'
             '(Кофейня — идеальное место для первых вежливых фраз.)',
     'content': {
         'speak_en': (
             'Britain drinks about 98 million cups of coffee a day. '
             'A café is a perfect place for your first polite phrases.'
         ),
     }},
    {'type': 'exercise', 'skill': 'vocabulary',
     'text': 'Выбери правильный перевод:',
     'content': {
         'exercise_type': 'matching',
         'pairs': [
             {'left': 'coffee', 'right': 'кофе'},
             {'left': 'tea', 'right': 'чай'},
             {'left': 'please', 'right': 'пожалуйста'},
             {'left': 'thank you', 'right': 'спасибо'},
         ],
         'distractors': ['чашка', 'меню', 'сахар'],
         'explanation': 'Запомни переводы — они пригодятся в заказе.',
     }},
    {'type': 'exercise', 'skill': 'grammar',
     'text': 'Верно или нет?\n\n«I want a coffee» — вежливая фраза для кафе.',
     'content': {'exercise_type': 'true_false',
                 'options': ['Верно', 'Неверно'],
                 'correct': ['Неверно'],
                 'explanation': 'Грубовато. Лучше: «I would like a coffee, please.»',
                 'rule_key': 'polite-requests',
                 'hint_detail_ru': _COFFEE_HINT_POLITE}},
    {'type': 'exercise', 'skill': 'grammar',
     'text': 'Заполни пропуск:\n\nI ___ like a tea, please.',
     'content': {'exercise_type': 'fill_gap', 'correct': ['would'],
                 'rule_key': 'polite-requests',
                 'hint_detail_ru': (
                     '💡 Нужно слово <b>would</b> — вместе с <b>like</b> это вежливое '
                     '«хотел(а) бы»: <b>would like</b>.'
                 ),
                 'explanation': 'would like = вежливое «хотел бы».'}},
    {'type': 'exercise', 'skill': 'grammar',
     'text': 'Собери фразу из слов:\n\nlike / a / I / coffee / would / please',
     'content': {'exercise_type': 'word_order',
                 'rule_key': 'polite-requests',
                 'hint_detail_ru': _COFFEE_HINT_POLITE,
                 'correct': ['i would like a coffee please'],
                 'explanation': 'I would like a coffee, please.'}},
    {'type': 'speaking', 'skill': 'speaking',
     'text': 'Теперь скажи вслух свой заказ:',
     'content': {'target': 'A cup of coffee, please.'}},
    {'type': 'exercise', 'skill': 'vocabulary',
     'text': 'Том спрашивает:\n'
             '🇬🇧 Anything else?\n'
             '(Ещё что-нибудь?)\n\n'
             'Как вежливо сказать «Нет, спасибо»?',
     'content': {'exercise_type': 'multiple_choice',
                 'options': ['No.', 'No, thank you.', 'Not.'],
                 'correct': ['No, thank you.'],
                 'hint_detail_ru': (
                     '💡 Вежливый отказ: <b>No, thank you</b> — «Нет, спасибо». '
                     'Просто «No» звучит сухо.'
                 ),
                 'explanation': '«No, thank you» — вежливый отказ.'}},
    {'type': 'reflection',
     'text': '🧠 <b>Совет:</b> не бойся ошибок. Мозг запоминает язык быстрее, '
             'когда ты говоришь вслух — даже с ошибками. Каждая попытка '
             'приближает к цели.'},
    {'type': 'reward',
     'text': '🎉 <b>Эпизод пройден!</b>\n\n'
             'Ты сделал свой первый заказ в Лондоне! +XP, новые слова — в словаре, '
             'правило «Вежливые просьбы» — в библиотеке.'},
    {'type': 'cliffhanger',
     'text': '✈️ Эмма улыбается:\n'
             '🇬🇧 Tomorrow you fly to Manchester — and you\'ll meet someone on the plane.\n'
             '(Завтра ты летишь в Манчестер — и познакомишься с кем-то в самолёте.)\n\n'
             'Что сказать соседу в самолёте? Об этом — в <b>эпизоде 2</b>…',
     'content': {
         'speak_en': (
             'Tomorrow you fly to Manchester — and you\'ll meet someone on the plane.'
         ),
     }},
]

_FOOD_STEPS = [
    {'type': 'hook',
     'text': 'Ты в кафе и очень голоден 🍽️ Сейчас научимся заказывать еду и '
             'просить счёт — без стресса.'},
    {'type': 'vocabulary', 'skill': 'vocabulary',
     'content': {'words': [
         {'en': 'menu', 'ru': 'меню', 'example': 'Can I see the menu, please?',
          'example_ru': 'Можно меню, пожалуйста?'},
         {'en': 'order', 'ru': 'заказ / заказывать', 'example': 'I would like to order.',
          'example_ru': 'Я бы хотел сделать заказ.'},
         {'en': 'bill', 'ru': 'счёт', 'example': 'Can I have the bill, please?',
          'example_ru': 'Можно счёт, пожалуйста?'},
         {'en': 'delicious', 'ru': 'вкусно', 'example': 'It was delicious!',
          'example_ru': 'Было очень вкусно!'},
     ]}},
    {'type': 'grammar_note', 'skill': 'grammar', 'title': 'Универсальная просьба',
     'content': {
         'rule_ru': '«Can I have …, please?» — вежливая просьба, которая работает '
                    'почти везде: в кафе, в магазине, в отеле.',
         'table': {
             'headers': ['Ситуация', 'Фраза', 'Перевод'],
             'rows': [
                 ['В кафе', 'Can I have the menu, please?', 'Можно меню?'],
                 ['Счёт', 'Can I have the bill, please?', 'Можно счёт?'],
                 ['В магазине', 'Can I have a bag, please?', 'Можно пакет?'],
             ],
         },
         'examples': [
             {'en': 'Can I have some water, please?', 'ru': 'Можно воды, пожалуйста?'},
         ],
         'tip_ru': 'Формула: Can I have + что-то + please.',
         'rule_key': 'polite-requests',
     }},
    {'type': 'exercise', 'skill': 'vocabulary',
     'text': 'Как попросить счёт?',
     'content': {'exercise_type': 'multiple_choice',
                 'options': ['Give bill.', 'Can I have the bill, please?', 'Money now.'],
                 'correct': ['Can I have the bill, please?'],
                 'explanation': 'Can I have …, please? — вежливо и естественно.'}},
    {'type': 'speaking', 'skill': 'speaking',
     'text': 'Скажи вслух, что блюдо было вкусным:',
     'content': {'target': 'It was delicious, thank you!'}},
    {'type': 'exercise', 'skill': 'writing',
     'text': 'Напиши, что бы ты заказал в кафе (1 предложение на английском).',
     'content': {'exercise_type': 'writing',
                 'ai_check_prompt': 'A1 cafe order. Be kind; at most one key fix.'}},
    {'type': 'reflection',
     'text': 'Теперь ты закажешь еду и попросишь счёт в любом кафе. 👏'},
    {'type': 'reward', 'text': 'Ужин заказан по-английски! 🍝🎉'},
]

_PLANE_STEPS = [
    {'type': 'hook',
     'text': '✈️ Эпизод 2. Рейс в Манчестер.\n\n'
             'Ты садишься в кресло у окна. Рядом опускается попутчица, улыбается '
             'и говорит: «Hi! Is this seat taken?» Сейчас научимся знакомиться и '
             'вести small talk — так, чтобы было легко и приятно.'},
    {'type': 'story', 'with_character': True,
     'text': '📖 Соседку зовут Sophie. Она летит на конференцию и обожает '
             'знакомиться с новыми людьми. «Where are you from?» — спрашивает она '
             'с улыбкой. Пора ответить.'},
    {'type': 'vocabulary', 'skill': 'vocabulary',
     'content': {'words': [
         {'en': 'seat', 'ru': 'место', 'example': 'Is this seat taken?',
          'example_ru': 'Это место занято?'},
         {'en': 'flight', 'ru': 'рейс', 'example': 'It is a long flight.',
          'example_ru': 'Это долгий рейс.'},
         {'en': 'trip', 'ru': 'поездка', 'example': 'Have a nice trip!',
          'example_ru': 'Хорошей поездки!'},
         {'en': 'nice to meet you', 'ru': 'приятно познакомиться',
          'example': 'Nice to meet you!', 'example_ru': 'Приятно познакомиться!'},
     ]}},
    {'type': 'grammar_note', 'skill': 'grammar', 'title': 'Вопросы в Present Simple',
     'content': {
         'rule_ru': 'Чтобы задать вопрос в настоящем времени, ставим do/does в '
                    'начало: do + подлежащее + глагол. Для he/she/it используем does.',
         'table': {
             'headers': ['Кто', 'Вопрос', 'Перевод'],
             'rows': [
                 ['I / you / we / they', 'Where do you live?', 'Где ты живёшь?'],
                 ['he / she / it', 'Where does he work?', 'Где он работает?'],
                 ['to be', 'Where are you from?', 'Откуда ты?'],
             ],
         },
         'examples': [
             {'en': 'What do you do?', 'ru': 'Чем ты занимаешься?'},
             {'en': 'Do you like tea?', 'ru': 'Ты любишь чай?'},
         ],
         'tip_ru': 'С глаголом to be (am/is/are) do не нужен: «Are you from Russia?»',
         'rule_key': 'present-simple-questions',
     }},
    {'type': 'exercise', 'skill': 'grammar',
     'text': 'Собери вопрос из слов: from / are / where / you',
     'content': {'exercise_type': 'word_order',
                 'correct': ['where are you from'],
                 'explanation': 'Where are you from? — Откуда ты?'}},
    {'type': 'dialogue', 'skill': 'reading',
     'text': 'Послушай, как знакомятся Sophie и попутчик:',
     'content': {'lines': [
         {'speaker': 'Sophie', 'text': "Hi! Is this seat taken?",
          'ru': 'Привет! Это место занято?'},
         {'speaker': 'You', 'text': "No, it's free. Please sit down.",
          'ru': 'Нет, свободно. Садитесь, пожалуйста.'},
         {'speaker': 'Sophie', 'text': "I'm Sophie. Nice to meet you!",
          'ru': 'Я Софи. Приятно познакомиться!'},
         {'speaker': 'You', 'text': "Nice to meet you too!",
          'ru': 'Мне тоже приятно!'},
     ]}},
    {'type': 'exercise', 'skill': 'vocabulary',
     'text': 'Как ответить на «Nice to meet you»?',
     'content': {'exercise_type': 'multiple_choice',
                 'options': ['Nice to meet you too!', 'Yes.', 'Thank you bye.'],
                 'correct': ['Nice to meet you too!'],
                 'explanation': 'Отвечаем тем же: «Nice to meet you too!»'}},
    {'type': 'ai_dialogue', 'skill': 'speaking', 'with_character': True,
     'content': {'opening': "Hi! Is this seat taken? I'm Sophie. What's your name?",
                 'situation': 'small talk between two passengers on a plane',
                 'turns': 4}},
    {'type': 'speaking', 'skill': 'speaking',
     'text': 'Представься вслух: скажи, как тебя зовут и откуда ты.',
     'content': {'target': 'My name is Alex. I am from Russia.'}},
    {'type': 'exercise', 'skill': 'vocabulary',
     'text': 'Небольшая практика из твоей сферы — задание подстроится под тебя:',
     'content': {'personalize': True, 'skill': 'vocabulary'}},
    {'type': 'exercise', 'skill': 'writing',
     'text': 'Напиши 1–2 предложения о себе на английском (имя, город, чем '
             'занимаешься).',
     'content': {'exercise_type': 'writing',
                 'ai_check_prompt': 'Beginner A2 self-introduction. Be kind; '
                                    'point out at most one key fix.'}},
    {'type': 'reflection',
     'text': '🧠 Психология общения: люди любят, когда им задают вопросы о них. '
             'Один искренний вопрос («Where are you from?») — и разговор пошёл.'},
    {'type': 'reward', 'text': '🗣️🎉 Ты познакомился с Sophie на английском и '
                               'рассказал о себе! Слова — в словаре, прогресс — растёт.'},
    {'type': 'cliffhanger',
     'text': '🏙️ В Манчестере тебя ждёт новая история: заселение в отель и первый '
             'рабочий разговор. Продолжение — в <b>эпизоде 3</b>…'},
]


_HOTEL_STEPS = [
    {'type': 'hook',
     'text': '🏨 <b>Эпизод 3. Hotel Check-in</b>\n\n'
             'Манчестер, вечер. Рейс позади, ты устал, но нужно заселиться. '
             'В лобби отеля очередь, слышны только английские фразы.\n\n'
             'Эмма писала: «Just say you have a reservation — they\'ll help you.» '
             'Сейчас проверим это на практике.'},
    {'type': 'story', 'with_character': True,
     'text': '📖 Ты подходишь к стойке. Молодой администратор <b>James</b> поднимает '
             'глаза и улыбается:\n'
             '«Good evening! How can I help you?»\n\n'
             'Глубокий вдох — твоя очередь.'},
    {'type': 'dialogue', 'skill': 'listening',
     'text': '💬 Типичный диалог на ресепшене:',
     'content': {'lines': [
         {'speaker': 'James', 'text': 'Good evening! Do you have a reservation?',
          'ru': 'Добрый вечер! У вас есть бронь?'},
         {'speaker': 'You', 'text': "Yes. I'd like to check in, please.",
          'ru': 'Да. Я бы хотел заселиться, пожалуйста.'},
         {'speaker': 'James', 'text': 'Of course. Your name, please?',
          'ru': 'Конечно. Ваше имя, пожалуйста?'},
         {'speaker': 'You', 'text': 'I have a reservation under Ivanov.',
          'ru': 'У меня бронь на имя Иванов.'},
         {'speaker': 'James', 'text': 'Perfect. Here is your key. Room 412.',
          'ru': 'Отлично. Вот ваш ключ. Номер 412.'},
     ]}},
    {'type': 'vocabulary', 'skill': 'vocabulary',
     'content': {'words': [
         {'en': 'reservation', 'ru': 'бронь', 'example': 'I have a reservation.',
          'example_ru': 'У меня есть бронь.'},
         {'en': 'check in', 'ru': 'заселиться', 'example': "I'd like to check in, please.",
          'example_ru': 'Я бы хотел заселиться.'},
         {'en': 'room', 'ru': 'номер', 'example': 'Your room is on the fourth floor.',
          'example_ru': 'Ваш номер на четвёртом этаже.'},
         {'en': 'key', 'ru': 'ключ', 'example': 'Here is your key.',
          'example_ru': 'Вот ваш ключ.'},
         {'en': 'lift', 'ru': 'лифт', 'example': 'The lift is on the left.',
          'example_ru': 'Лифт слева.'},
         {'en': 'breakfast', 'ru': 'завтрак', 'example': 'Breakfast is from seven to ten.',
          'example_ru': 'Завтрак с семи до десяти.'},
     ]}},
    {'type': 'story',
     'text': '🌍 <b>Факт:</b> в UK чаще говорят <b>lift</b>, в США — <b>elevator</b>. '
             'Оба варианта правильные — в Британии пригодится lift.'},
    {'type': 'grammar_note', 'skill': 'grammar', 'title': 'Заселение в отель',
     'content': {
         'rule_ru': 'На ресепшене: скажи, что хочешь заселиться, и назови имя в брони. '
                    'Could / I\'d like — вежливо и естественно.',
         'table': {
             'headers': ['Ситуация', 'Фраза', 'Перевод'],
             'rows': [
                 ['Заселение', "I'd like to check in, please.", 'Я бы хотел заселиться.'],
                 ['Бронь', 'I have a reservation under Ivanov.', 'Бронь на имя Иванов.'],
                 ['Ключ', 'Could I have the key, please?', 'Можно ключ, пожалуйста?'],
             ],
         },
         'examples': [
             {'en': 'I have a reservation for two nights.', 'ru': 'Бронь на две ночи.'},
             {'en': 'What time is breakfast?', 'ru': 'Во сколько завтрак?'},
         ],
         'tip_ru': 'Under + фамилия = «на имя …» в бронировании.',
         'rule_key': 'hotel-check-in',
     }},
    {'type': 'exercise', 'skill': 'vocabulary',
     'text': '🔗 Соедини слова с переводом:',
     'content': {
         'exercise_type': 'matching',
         'pairs': [
             {'left': 'reservation', 'right': 'бронь'},
             {'left': 'key', 'right': 'ключ'},
             {'left': 'breakfast', 'right': 'завтрак'},
             {'left': 'lift', 'right': 'лифт'},
         ],
         'distractors': ['счёт', 'меню', 'рейс'],
         'explanation': 'Эти слова — must-have в отеле.',
     }},
    {'type': 'exercise', 'skill': 'grammar',
     'text': 'Верно или нет?\n\n«I want room now» — нормальная фраза на ресепшене.',
     'content': {'exercise_type': 'true_false',
                 'options': ['Верно', 'Неверно'],
                 'correct': ['Неверно'],
                 'explanation': "Лучше: «I'd like to check in, please.»"}},
    {'type': 'exercise', 'skill': 'vocabulary',
     'text': 'James: «Do you have a reservation?» Что ответить?',
     'content': {'exercise_type': 'multiple_choice',
                 'options': ['Yes. I would like to check in, please.',
                             'Give room.',
                             'Reservation no.'],
                 'correct': ['Yes. I would like to check in, please.'],
                 'explanation': 'Подтверди бронь и скажи, что хочешь заселиться.'}},
    {'type': 'exercise', 'skill': 'grammar',
     'text': 'Заполни пропуск:\n\nI have a ___ under Ivanov.',
     'content': {'exercise_type': 'fill_gap', 'correct': ['reservation'],
                 'explanation': 'reservation = бронь.'}},
    {'type': 'exercise', 'skill': 'grammar',
     'text': 'Собери фразу:\n\nto / check / I / in / would / like / please',
     'content': {'exercise_type': 'word_order',
                 'correct': ['i would like to check in please'],
                 'explanation': "I'd like to check in, please."}},
    {'type': 'speaking', 'skill': 'speaking',
     'text': 'Скажи вслух на ресепшене:',
     'content': {'target': 'I have a reservation under Ivanov.'}},
    {'type': 'exercise', 'skill': 'vocabulary',
     'text': 'Практика из твоей сферы — задание подстроится под тебя:',
     'content': {'personalize': True, 'skill': 'vocabulary'}},
    {'type': 'reflection',
     'text': '🧠 <b>Совет:</b> на ресепшене говори коротко и вежливо. '
             'Достаточно трёх фраз: check in → имя в брони → спасибо.'},
    {'type': 'reward',
     'text': '🏨🎉 <b>Эпизод пройден!</b>\n\n'
             'Ты заселился в отель в Манчестере! Новые слова — в словаре, '
             'правило «Заселение в отель» — в библиотеке.'},
    {'type': 'cliffhanger',
     'text': '💼 Завтра — первый рабочий день. Коллеги заговорят с тобой за кофе. '
             'Что сказать о своей работе?\n\n'
             'Продолжение — в <b>эпизоде 4</b>…'},
]


# --------------------------------------------------------------------------- #
# Curriculum: units grouping lessons per level.
# --------------------------------------------------------------------------- #

CURRICULUM = [
    {
        'unit': {'slug': 'a1-city-basics', 'title': 'Первые шаги в городе',
                 'level': 'a1', 'order': 1,
                 'description': 'Кафе, заказы, вежливые просьбы.'},
        'lessons': [
            {'title': 'Coffee in London', 'order': 1, 'is_trial': True,
             'subtitle': 'Закажи кофе как местный', 'intro': '▶️ Эпизод 1 — Coffee in London',
             'xp': 80, 'tags': ['travel', 'food and drink'], 'steps': _COFFEE_STEPS},
            {'title': 'Ordering Food', 'order': 2, 'is_trial': False,
             'subtitle': 'Заказать еду и попросить счёт',
             'intro': 'Урок 3 — «Заказ еды»', 'xp': 60,
             'tags': ['travel', 'food and drink'], 'steps': _FOOD_STEPS},
        ],
    },
    {
        'unit': {'slug': 'a2-meeting-people', 'title': 'Знакомства и общение',
                 'level': 'a2', 'order': 1,
                 'description': 'Small talk, знакомство, рассказ о себе.'},
        'lessons': [
            {'title': 'Meeting on a Plane', 'order': 1, 'is_trial': True,
             'subtitle': 'Знакомство и small talk',
             'intro': '▶️ Эпизод 2 — Meeting on a Plane', 'xp': 80,
             'tags': ['travel', 'communication'], 'steps': _PLANE_STEPS},
        ],
    },
    {
        'unit': {'slug': 'a2-manchester-hotel', 'title': 'Манчестер: отель',
                 'level': 'a2', 'order': 2,
                 'description': 'Заселение, номер, ориентирование в отеле.'},
        'lessons': [
            {'title': 'Hotel Check-in', 'order': 1, 'is_trial': False,
             'subtitle': 'Заселение в отель',
             'intro': '▶️ Эпизод 3 — Hotel Check-in',
             'xp': 90, 'minutes': 12,
             'tags': ['travel', 'work'], 'steps': _HOTEL_STEPS},
        ],
    },
]


def _build_lesson(unit, character, level, data):
    lesson, _ = Lesson.objects.update_or_create(
        title=data['title'],
        defaults=dict(
            unit=unit, level=level, order=data['order'],
            is_trial=data['is_trial'], is_published=True,
            subtitle=data.get('subtitle', ''), intro_text=data.get('intro', ''),
            outro_text=data.get('outro', ''), xp_reward=data.get('xp', 60),
            character=character, estimated_minutes=data.get('minutes', 8),
            tags=data.get('tags', []),
        ),
    )
    lesson.steps.all().delete()
    for i, step in enumerate(data['steps'], start=1):
        LessonStep.objects.create(
            lesson=lesson, order=i,
            step_type=step['type'],
            title=step.get('title', ''),
            text=step.get('text', ''),
            skill=step.get('skill', 'mixed'),
            content=step.get('content', {}),
            xp_reward=step.get('xp', 10),
            character=character if step.get('with_character') else None,
        )
    return lesson


def seed_curriculum():
    """Create/refresh all units and lessons. Idempotent."""
    emma = Character.objects.filter(name='Emma').first()
    Character.objects.update_or_create(
        name='James',
        defaults={
            'role': 'администратор отеля в Манчестере',
            'personality': 'calm, professional, friendly, patient',
        },
    )
    james = Character.objects.filter(name='James').first()
    for block in CURRICULUM:
        u = block['unit']
        unit, _ = Unit.objects.update_or_create(
            slug=u['slug'],
            defaults={'title': u['title'], 'level': u['level'],
                      'order': u['order'], 'description': u.get('description', ''),
                      'is_published': True},
        )
        for lesson_data in block['lessons']:
            char = emma
            if lesson_data['title'] == 'Hotel Check-in':
                char = james
            _build_lesson(unit, char, u['level'], lesson_data)
