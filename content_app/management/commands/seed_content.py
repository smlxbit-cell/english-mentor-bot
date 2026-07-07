"""Seed base data: achievements, interests, Emma, the adaptive diagnostic, and
the curriculum (units + lessons live in content_app.curriculum).

Idempotent: safe to run multiple times.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from content_app.models import Character, DiagnosticItem
from gamification_app.models import Achievement
from users_app.models import Interest


class Command(BaseCommand):
    help = 'Seed achievements, interests, diagnostic items and the curriculum.'

    def handle(self, *args, **options):
        from content_app.curriculum import seed_curriculum

        self.seed_achievements()
        self.seed_interests()
        self.seed_character()
        self.seed_diagnostic()
        seed_curriculum()
        from content_app.grammar_rules import seed_grammar_rules
        n = seed_grammar_rules()
        self.stdout.write(self.style.SUCCESS(f'Grammar rules: {n} published in library.'))
        self.stdout.write(self.style.SUCCESS('Content seeded successfully.'))

    def seed_interests(self):
        names = [
            'Путешествия', 'Кино и сериалы', 'Музыка', 'Игры',
            'Спорт', 'Книги', 'Искусство', 'Природа',
            'Работа и карьера', 'Бизнес', 'Технологии', 'Наука',
            'Еда и кухня', 'Мода', 'Психология', 'История',
        ]
        for name in names:
            Interest.objects.get_or_create(
                slug=slugify(name, allow_unicode=True),
                defaults={'name': name},
            )

    def seed_achievements(self):
        achievements = [
            ('first-session', 'Первый шаг', '🌱', 20),
            ('three-day-streak', 'В огне', '🔥', 50),
            ('first-story', 'Исследователь историй', '📖', 30),
            ('ten-correct-answers', 'Острый ум', '🧠', 40),
            ('first-ai-dialogue', 'Первый разговор', '🗣️', 30),
        ]
        for code, title, icon, xp in achievements:
            Achievement.objects.update_or_create(
                code=code,
                defaults={'title': title, 'icon': icon, 'xp_reward': xp, 'is_active': True},
            )

    def seed_character(self):
        emma, _ = Character.objects.update_or_create(
            name='Emma',
            defaults={
                'role': 'дружелюбный гид по Лондону',
                'personality': 'warm, patient, encouraging, a little playful',
                'speaking_style': 'simple, natural, 1-2 short sentences',
            },
        )
        Character.objects.update_or_create(
            name='Spirit',
            defaults={
                'role': 'дух английского языка — спутник и собеседник ученика',
                'personality': (
                    'warm, playful, curious, magical but grounded; has opinions, '
                    'friends, and daily mini-adventures; never shames mistakes'
                ),
                'speaking_style': (
                    'first person as Spirit; short vivid stories; simple English phrases '
                    'with Russian translation for learners'
                ),
            },
        )
        return emma

    def seed_diagnostic(self):
        # All items — Russian context; mix of buttons, typing, and voice.
        items = [
            # A1
            dict(level='a1', skill='grammar', item_type='multiple_choice', order=1,
                 prompt='«Я — студент»\n\nI ___ a student.',
                 options=['am', 'is', 'are'], correct=['am'],
                 explanation_ru='С <b>I</b> всегда <b>am</b>: I am a student.'),
            dict(level='a1', skill='vocabulary', item_type='multiple_choice', order=2,
                 prompt='Как по-английски «кофе»?',
                 options=['coffee', 'tea', 'water'], correct=['coffee']),
            dict(level='a1', skill='grammar', item_type='multiple_choice', order=3,
                 prompt='«Она счастлива»\n\nShe ___ happy.',
                 options=['is', 'are', 'am'], correct=['is'],
                 explanation_ru='С <b>she</b> → <b>is</b>: She is happy.'),
            dict(level='a1', skill='vocabulary', item_type='multiple_choice', order=4,
                 prompt='«Книга» по-английски:',
                 options=['book', 'door', 'bag'], correct=['book']),
            # A2
            dict(level='a2', skill='grammar', item_type='multiple_choice', order=1,
                 prompt='«Она пьёт кофе каждое утро»\n\nShe ___ coffee every morning.',
                 options=['drinks', 'drink', 'drinking'], correct=['drinks'],
                 explanation_ru='She/he/it + глагол с <b>-s</b>: she drinks.'),
            dict(level='a2', skill='grammar', item_type='multiple_choice', order=2,
                 prompt='«Я был дома вчера» — как правильно?',
                 options=[
                     'I was at home yesterday',
                     'I am at home yesterday',
                     'I will at home yesterday',
                 ],
                 correct=['I was at home yesterday'],
                 explanation_ru='Прошлое: <b>I was</b> at home yesterday.'),
            dict(level='a2', skill='grammar', item_type='multiple_choice', order=3,
                 prompt='«Они ездят на работу на автобусе»\n\nThey ___ to work by bus.',
                 options=['go', 'goes', 'going'], correct=['go'],
                 explanation_ru='They → глагол без <b>-s</b>: they go.'),
            dict(level='a2', skill='vocabulary', item_type='multiple_choice', order=4,
                 prompt='«Библиотека» по-английски:',
                 options=['library', 'hospital', 'station'], correct=['library']),
            # B1
            dict(level='b1', skill='grammar', item_type='multiple_choice', order=1,
                 prompt=(
                     '«Если бы у меня было больше времени, я бы путешествовал»\n\n'
                     'If I ___ more time, I would travel.'
                 ),
                 options=['had', 'have', 'has', 'will have'], correct=['had'],
                 explanation_ru='Нереальное «если бы» → <b>If I had</b>…, I would…'),
            dict(level='b1', skill='grammar', item_type='multiple_choice', order=2,
                 prompt='«Я живу здесь с 2010 года»\n\nI\'ve lived here ___ 2010.',
                 options=['since', 'for', 'from'], correct=['since'],
                 explanation_ru='<b>Since</b> + год начала. <b>For</b> + длительность (for 5 years).'),
            dict(level='b1', skill='vocabulary', item_type='multiple_choice', order=3,
                 prompt='«Я бы хотел(а) чашку кофе» — как сказать?',
                 options=[
                     'I would like a cup of coffee',
                     'I am like a cup of coffee',
                     'I would liking coffee',
                 ],
                 correct=['I would like a cup of coffee'],
                 explanation_ru='Вежливая просьба: <b>I would like…</b>'),
            dict(level='b1', skill='reading', item_type='multiple_choice', order=4,
                 prompt='«She has already finished her work»\n\nОна уже закончила работу — это время…',
                 options=['Present Perfect', 'Past Simple', 'Future'],
                 correct=['Present Perfect'],
                 explanation_ru='<b>Has finished</b> = Present Perfect (уже сделала).'),
            # B2
            dict(level='b2', skill='grammar', item_type='multiple_choice', order=1,
                 prompt=(
                     '«С нетерпением жду встречи с тобой»\n\n'
                     'I look forward to ___ you soon.'
                 ),
                 options=['seeing', 'see', 'saw'], correct=['seeing'],
                 explanation_ru=(
                     'Устойчиво: <b>look forward to + -ing</b>. '
                     'I look forward to <b>seeing</b> you.'
                 )),
            dict(level='b2', skill='vocabulary', item_type='multiple_choice', order=2,
                 prompt='«Несмотря на дождь, мы пошли гулять»\n\nDespite ___',
                 options=['the rain', 'rainy', 'raining'], correct=['the rain', 'rain'],
                 explanation_ru='После <b>despite</b> — существительное: <b>the rain</b>, не <b>rainy</b>.'),
            dict(level='b2', skill='grammar', item_type='multiple_choice', order=3,
                 prompt='«Она предложила уйти пораньше»\n\nShe suggested ___ earlier.',
                 options=['leaving', 'leave', 'to leave', 'left'], correct=['leaving', 'to leave'],
                 explanation_ru=(
                     'После <b>suggest</b> обычно <b>-ing</b>: '
                     '<b>She suggested leaving</b> = она предложила уйти.'
                 )),
            dict(level='b2', skill='reading', item_type='multiple_choice', order=4,
                 prompt='«I wish I spoke English fluently»\n\nЧеловек хочет…',
                 options=[
                     'говорить по-английски лучше',
                     'говорил только в прошлом',
                     'бросить учить язык',
                 ],
                 correct=['говорить по-английски лучше']),
            # Extra — typing & speaking (always with Russian context)
            dict(level='a1', skill='vocabulary', item_type='translation_ru_en', order=5,
                 prompt='Переведи на английский:\n\n«Привет!»',
                 correct=['hello', 'hi', 'hello!'],
                 keywords=['hello'],
                 explanation_ru='Hello / Hi = привет.'),
            dict(level='a2', skill='vocabulary', item_type='translation_ru_en', order=5,
                 prompt='Переведи на английский:\n\n«Мне нравится чай»',
                 correct=['i like tea', 'i like the tea'],
                 keywords=['like', 'tea'],
                 explanation_ru='I like tea = мне нравится чай.'),
            dict(level='a2', skill='speaking', item_type='speaking', order=6,
                 prompt='«Кофе, пожалуйста»\n\nКак сказать по-английски?',
                 keywords=['coffee', 'please'],
                 explanation_ru='Coffee, please.'),
            dict(level='b1', skill='grammar', item_type='fill_gap', order=5,
                 prompt=(
                     '«Если бы у меня было больше времени, я бы путешествовал»\n\n'
                     'If I ___ more time, I would travel.'
                 ),
                 correct=['had'],
                 explanation_ru='Нереальное сейчас: <b>If I had</b> more time…'),
            dict(level='b1', skill='vocabulary', item_type='translation_ru_en', order=6,
                 prompt='Переведи на английский:\n\n«Мне нужна помощь»',
                 correct=['i need help', 'i need some help'],
                 keywords=['need', 'help'],
                 explanation_ru='I need help = мне нужна помощь.'),
            dict(level='b2', skill='grammar', item_type='fill_gap', order=5,
                 prompt=(
                     '«Она предложила уйти пораньше»\n\n'
                     'She suggested ___ earlier.'
                 ),
                 correct=['leaving', 'to leave'],
                 explanation_ru='She suggested <b>leaving</b> = она предложила уйти.'),
            dict(level='b2', skill='speaking', item_type='speaking', order=6,
                 prompt='«Я согласен»\n\nКак сказать по-английски?',
                 keywords=['agree', 'i agree'],
                 explanation_ru='I agree = я согласен.'),
            dict(level='a2', skill='listening', item_type='listening', order=7,
                 prompt=(
                     '🎧 Listen: «I would like a table for two, please.»\n\n'
                     'Что хочет человек?'
                 ),
                 options=['A table for two', 'A coffee to go', 'A hotel room'],
                 correct=['A table for two', 'a table for two'],
                 explanation_ru='Table for two = столик на двоих.'),
            dict(level='b1', skill='listening', item_type='listening', order=7,
                 prompt=(
                     '🎧 Listen: «Could you send me the report by Friday?»\n\n'
                     'О чём просьба?'
                 ),
                 options=['Send a report by Friday', 'Meet on Friday', 'Call on Friday'],
                 correct=['Send a report by Friday', 'send me the report by friday'],
                 explanation_ru='Send the report by Friday = прислать отчёт к пятнице.'),
            dict(level='b2', skill='listening', item_type='listening', order=7,
                 prompt=(
                     '🎧 Listen: «Despite the rain, we enjoyed the walk.»\n\n'
                     'Как прошла прогулка?'
                 ),
                 options=['They enjoyed it despite rain', 'They stayed home', 'It was cancelled'],
                 correct=['They enjoyed it despite rain', 'they enjoyed the walk'],
                 explanation_ru='Despite the rain = несмотря на дождь — всё равно понравилось.'),
        ]
        active_keys = {(d['level'], d['order'], d['skill']) for d in items}
        for data in items:
            DiagnosticItem.objects.update_or_create(
                level=data['level'], order=data['order'], skill=data['skill'],
                defaults={**data, 'is_active': True},
            )
        for item in DiagnosticItem.objects.all():
            key = (item.level, item.order, item.skill)
            if key not in active_keys:
                item.is_active = False
                item.save(update_fields=['is_active'])
