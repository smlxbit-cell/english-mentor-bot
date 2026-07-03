from django.core.management.base import BaseCommand

from users_app.models import Interest
from content_app.models import (
    Character,
    ContentTheme,
    Phrase,
    StoryArc,
    StoryEpisode,
)
from gamification_app.models import Achievement


class Command(BaseCommand):
    help = 'Create demo data for English mentor bot'

    def handle(self, *args, **options):
        self.create_interests()
        self.create_themes()
        self.create_phrases()
        self.create_characters()
        self.create_story()
        self.create_achievements()

        self.stdout.write(
            self.style.SUCCESS('Demo data created successfully.')
        )

    def create_interests(self):
        interests = [
            ('Travel', 'travel'),
            ('Work', 'work'),
            ('Movies and series', 'movies-series'),
            ('Music', 'music'),
            ('Games', 'games'),
            ('Business', 'business'),
            ('IT and technology', 'it-technology'),
            ('Food', 'food'),
            ('Daily life', 'daily-life'),
            ('Communication', 'communication'),
        ]

        for name, slug in interests:
            Interest.objects.update_or_create(
                slug=slug,
                defaults={'name': name},
            )

    def create_themes(self):
        themes = [
            ('Daily life', 'daily-life'),
            ('Travel', 'travel'),
            ('Work communication', 'work-communication'),
            ('Cafe and restaurants', 'cafe-restaurants'),
            ('Small talk', 'small-talk'),
            ('Technology', 'technology'),
        ]

        for name, slug in themes:
            ContentTheme.objects.update_or_create(
                slug=slug,
                defaults={'name': name},
            )

    def create_phrases(self):
        daily_life = ContentTheme.objects.get(slug='daily-life')
        travel = ContentTheme.objects.get(slug='travel')
        cafe = ContentTheme.objects.get(slug='cafe-restaurants')
        small_talk = ContentTheme.objects.get(slug='small-talk')

        phrases = [
            {
                'english_text': 'How are you doing?',
                'translation': 'Как дела?',
                'explanation': 'Неформальный способ спросить, как у человека дела.',
                'level': 'A1',
                'theme': small_talk,
            },
            {
                'english_text': 'I would like a coffee, please.',
                'translation': 'Я бы хотел кофе, пожалуйста.',
                'explanation': 'Вежливая фраза для заказа.',
                'level': 'A1',
                'theme': cafe,
            },
            {
                'english_text': 'Could you help me?',
                'translation': 'Не могли бы вы мне помочь?',
                'explanation': 'Вежливая просьба о помощи.',
                'level': 'A1',
                'theme': daily_life,
            },
            {
                'english_text': 'Where is the nearest station?',
                'translation': 'Где ближайшая станция?',
                'explanation': 'Полезная фраза в путешествии.',
                'level': 'A1',
                'theme': travel,
            },
            {
                'english_text': 'I am looking for this address.',
                'translation': 'Я ищу этот адрес.',
                'explanation': 'Фраза для ситуации в городе.',
                'level': 'A2',
                'theme': travel,
            },
        ]

        for phrase in phrases:
            Phrase.objects.update_or_create(
                english_text=phrase['english_text'],
                defaults=phrase,
            )

    def create_characters(self):
        characters = [
            {
                'name': 'Emma',
                'role': 'Friendly local guide',
                'personality': 'Helpful, calm, positive.',
            },
            {
                'name': 'Jack',
                'role': 'English learner',
                'personality': 'Curious, sometimes confused, but motivated.',
            },
        ]

        for character in characters:
            Character.objects.update_or_create(
                name=character['name'],
                defaults=character,
            )

    def create_story(self):
        travel_theme = ContentTheme.objects.get(slug='travel')

        arc, _ = StoryArc.objects.update_or_create(
            slug='first-day-in-london',
            defaults={
                'title': 'First Day in London',
                'description': 'A beginner-friendly story about arriving in a new city.',
                'is_active': True,
            },
        )

        episode, _ = StoryEpisode.objects.update_or_create(
            arc=arc,
            episode_number=1,
            defaults={
                'title': 'At the Station',
                'level': 'A1',
                'theme': travel_theme,
                'short_summary': 'Jack arrives in London and asks Emma for help.',
                'story_text': (
                    'Jack arrives at the station. He has a small suitcase and a map. '
                    'He looks confused. Emma sees him and smiles.\n\n'
                    'Emma: Hi! Are you okay?\n'
                    'Jack: Hi. Could you help me?\n'
                    'Emma: Of course. What are you looking for?\n'
                    'Jack: I am looking for this address.\n'
                    'Emma: No problem. The nearest bus stop is over there.'
                ),
                'choices': [
                    {
                        'question': 'What does Jack need?',
                        'options': [
                            'He needs help.',
                            'He wants coffee.',
                            'He is buying a ticket.',
                        ],
                        'correct_answer': 'He needs help.',
                    }
                ],
                'target_words': [
                    'station',
                    'suitcase',
                    'map',
                    'address',
                    'bus stop',
                ],
                'is_published': True,
            },
        )

        characters = Character.objects.filter(name__in=['Emma', 'Jack'])
        episode.characters.set(characters)

        phrases = Phrase.objects.filter(
            english_text__in=[
                'Could you help me?',
                'I am looking for this address.',
                'Where is the nearest station?',
            ]
        )
        episode.target_phrases.set(phrases)

    def create_achievements(self):
        achievements = [
            {
                'code': 'first-session',
                'title': 'First Step',
                'description': 'Complete your first learning session.',
                'icon': '🌱',
                'xp_reward': 20,
                'is_active': True,
            },
            {
                'code': 'three-day-streak',
                'title': 'On Fire',
                'description': 'Study for 3 days in a row.',
                'icon': '🔥',
                'xp_reward': 50,
                'is_active': True,
            },
            {
                'code': 'first-story',
                'title': 'Story Explorer',
                'description': 'Complete your first story episode.',
                'icon': '📖',
                'xp_reward': 30,
                'is_active': True,
            },
            {
                'code': 'ten-correct-answers',
                'title': 'Sharp Mind',
                'description': 'Give 10 correct answers.',
                'icon': '🧠',
                'xp_reward': 40,
                'is_active': True,
            },
        ]

        for achievement in achievements:
            Achievement.objects.update_or_create(
                code=achievement['code'],
                defaults=achievement,
            )
