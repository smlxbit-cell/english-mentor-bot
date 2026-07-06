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
            'Путешествия', 'Кино и сериалы', 'Музыка', 'Работа и карьера',
            'Технологии', 'Спорт', 'Еда и кухня', 'Игры',
            'Книги', 'Бизнес', 'Наука', 'Мода',
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
                'role': 'языковой дух — спутник ученика',
                'personality': 'warm, playful, encouraging, never judges mistakes',
                'speaking_style': 'short, friendly, simple English',
            },
        )
        return emma

    def seed_diagnostic(self):
        items = [
            dict(level='a1', skill='grammar', item_type='multiple_choice', order=1,
                 prompt='I ___ a student.', options=['am', 'is', 'are'],
                 correct=['am']),
            dict(level='a1', skill='vocabulary', item_type='multiple_choice', order=2,
                 prompt="Выбери перевод слова «coffee»:",
                 options=['кофе', 'чай', 'вода'], correct=['кофе']),
            dict(level='a2', skill='grammar', item_type='multiple_choice', order=1,
                 prompt='She ___ coffee every morning.',
                 options=['drink', 'drinks', 'drinking'], correct=['drinks']),
            dict(level='a2', skill='vocabulary', item_type='translation_ru_en', order=2,
                 prompt='Переведи на английский: «Я был дома вчера».',
                 correct=['i was at home yesterday', 'i was home yesterday'],
                 keywords=['was', 'home', 'yesterday']),
            dict(level='b1', skill='grammar', item_type='fill_gap', order=1,
                 prompt='If I ___ more time, I would travel more. (вставь глагол)',
                 correct=['had']),
            dict(level='b1', skill='grammar', item_type='multiple_choice', order=2,
                 prompt="I've lived here ___ 2010.",
                 options=['since', 'for', 'from'], correct=['since']),
            dict(level='b2', skill='grammar', item_type='fill_gap', order=1,
                 prompt='I ___ studying English for two years. (Present Perfect Continuous)',
                 correct=['have been']),
            dict(level='b2', skill='vocabulary', item_type='multiple_choice', order=2,
                 prompt="Choose the most natural: 'I look forward to ___ you.'",
                 options=['see', 'seeing', 'saw'], correct=['seeing']),
            dict(level='a2', skill='speaking', item_type='speaking', order=3,
                 prompt='Задание на говорение.',
                 keywords=['cup', 'coffee', 'please']),
        ]
        for data in items:
            DiagnosticItem.objects.update_or_create(
                level=data['level'], order=data['order'], skill=data['skill'],
                defaults={**data, 'is_active': True},
            )
