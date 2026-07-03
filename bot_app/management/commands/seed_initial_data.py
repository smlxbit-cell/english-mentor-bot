from decimal import Decimal

from django.core.management.base import BaseCommand

from bot_app.models import DiagnosticQuestion, Lesson, SubscriptionPlan


class Command(BaseCommand):
    help = 'Seed initial diagnostic questions, lessons and subscription plans'

    def handle(self, *args, **options):
        self.seed_diagnostic_questions()
        self.seed_lessons()
        self.seed_subscription_plans()

        self.stdout.write(
            self.style.SUCCESS('Initial data seeded successfully.')
        )

    def seed_diagnostic_questions(self):
        questions = [
            {
                'text': 'Вставь правильное слово:\n\nI ___ Maria.',
                'correct_answer': 'am',
                'level': 'a1',
                'order': 1,
            },
            {
                'text': 'Вставь правильное слово:\n\nShe ___ coffee every morning.',
                'correct_answer': 'drinks',
                'level': 'a2',
                'order': 2,
            },
            {
                'text': 'Переведи на английский:\n\nЯ был/была дома вчера.',
                'correct_answer': 'i was at home yesterday|i was home yesterday',
                'level': 'a2',
                'order': 3,
            },
            {
                'text': 'Вставь правильное слово:\n\nIf I ___ more time, I would travel more.',
                'correct_answer': 'had',
                'level': 'b1',
                'order': 4,
            },
            {
                'text': 'Переведи на английский:\n\nЯ изучаю английский уже два года.',
                'correct_answer': 'i have been studying english for two years|i have studied english for two years',
                'level': 'b2',
                'order': 5,
            },
        ]

        for item in questions:
            DiagnosticQuestion.objects.update_or_create(
                order=item['order'],
                defaults=item,
            )

    def seed_lessons(self):
        lessons = [
            {
                'title': 'Урок 1. Знакомство',
                'level': 'a1',
                'content': (
                    'Урок 1. Знакомство\n\n'
                    'Фраза дня:\n'
                    'My name is Maria.\n'
                    'Меня зовут Мария.\n\n'
                    'Ещё примеры:\n'
                    'I am a student. — Я студентка/студент.\n'
                    'I am from Russia. — Я из России.\n\n'
                    'Задание:\n'
                    'Напиши по-английски: Меня зовут ...'
                ),
                'order': 1,
                'is_trial': True,
            },
            {
                'title': 'Урок 2. Напитки',
                'level': 'a1',
                'content': (
                    'Урок 2. Напитки\n\n'
                    'Фраза дня:\n'
                    'I would like tea, please.\n'
                    'Я бы хотел/хотела чай, пожалуйста.\n\n'
                    'Слова:\n'
                    'tea — чай\n'
                    'coffee — кофе\n'
                    'water — вода\n\n'
                    'Задание:\n'
                    'Переведи: Я бы хотела кофе, пожалуйста.'
                ),
                'order': 2,
                'is_trial': True,
            },
            {
                'title': 'Урок 3. Ежедневные действия',
                'level': 'a1',
                'content': (
                    'Урок 3. Ежедневные действия\n\n'
                    'I wake up at 8 o’clock.\n'
                    'Я просыпаюсь в 8 часов.\n\n'
                    'I drink coffee in the morning.\n'
                    'Я пью кофе утром.\n\n'
                    'Это уже платный урок.'
                ),
                'order': 3,
                'is_trial': False,
            },
            {
                'title': 'Урок 1. Present Simple',
                'level': 'a2',
                'content': (
                    'Урок 1. Present Simple\n\n'
                    'I work every day.\n'
                    'She works every day.\n\n'
                    'Не забывай про -s после he/she/it.\n\n'
                    'Задание:\n'
                    'Исправь ошибку: She work every day.'
                ),
                'order': 1,
                'is_trial': True,
            },
            {
                'title': 'Урок 2. Past Simple',
                'level': 'a2',
                'content': (
                    'Урок 2. Past Simple\n\n'
                    'I visited my friend yesterday.\n'
                    'Я навестил/навестила друга вчера.\n\n'
                    'Задание:\n'
                    'Переведи: Я смотрела фильм вчера.'
                ),
                'order': 2,
                'is_trial': True,
            },
            {
                'title': 'Урок 3. Future plans',
                'level': 'a2',
                'content': (
                    'Урок 3. Future plans\n\n'
                    'I am going to study English tonight.\n'
                    'Я собираюсь заниматься английским сегодня вечером.\n\n'
                    'Это уже платный урок.'
                ),
                'order': 3,
                'is_trial': False,
            },
            {
                'title': 'Урок 1. Talking about experience',
                'level': 'b1',
                'content': (
                    'Урок 1. Talking about experience\n\n'
                    'I have already visited London.\n'
                    'Я уже был/была в Лондоне.\n\n'
                    'Задание:\n'
                    'Напиши 2 предложения о своём опыте через Present Perfect.'
                ),
                'order': 1,
                'is_trial': True,
            },
            {
                'title': 'Урок 2. Giving opinions',
                'level': 'b1',
                'content': (
                    'Урок 2. Giving opinions\n\n'
                    'In my opinion, learning English should be practical.\n'
                    'По моему мнению, изучение английского должно быть практичным.\n\n'
                    'Задание:\n'
                    'Напиши своё мнение: English is important because...'
                ),
                'order': 2,
                'is_trial': True,
            },
            {
                'title': 'Урок 3. Conditional sentences',
                'level': 'b1',
                'content': (
                    'Урок 3. Conditional sentences\n\n'
                    'If I had more time, I would read more books.\n\n'
                    'Это уже платный урок.'
                ),
                'order': 3,
                'is_trial': False,
            },
            {
                'title': 'Урок 1. Advanced self-introduction',
                'level': 'b2',
                'content': (
                    'Урок 1. Advanced self-introduction\n\n'
                    'I have been working on improving my English for several years.\n\n'
                    'Задание:\n'
                    'Напиши расширенное представление о себе на 5–6 предложений.'
                ),
                'order': 1,
                'is_trial': True,
            },
            {
                'title': 'Урок 2. Nuance and accuracy',
                'level': 'b2',
                'content': (
                    'Урок 2. Nuance and accuracy\n\n'
                    'There is a subtle difference between "I did it" and "I have done it".\n\n'
                    'Задание:\n'
                    'Объясни разницу на своих примерах.'
                ),
                'order': 2,
                'is_trial': True,
            },
            {
                'title': 'Урок 3. Complex argumentation',
                'level': 'b2',
                'content': (
                    'Урок 3. Complex argumentation\n\n'
                    'Many learners struggle not with grammar itself, but with using it naturally.\n\n'
                    'Это уже платный урок.'
                ),
                'order': 3,
                'is_trial': False,
            },
        ]

        for item in lessons:
            Lesson.objects.update_or_create(
                level=item['level'],
                order=item['order'],
                defaults=item,
            )

    def seed_subscription_plans(self):
        SubscriptionPlan.objects.update_or_create(
            code='monthly',
            defaults={
                'name': 'Месячный доступ',
                'price': Decimal('990.00'),
                'currency': 'RUB',
                'period': 'monthly',
                'is_active': True,
            }
        )
