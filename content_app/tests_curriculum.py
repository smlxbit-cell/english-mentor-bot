"""Curriculum seed smoke tests."""

from django.test import TestCase

from content_app.curriculum import CURRICULUM, seed_curriculum
from content_app.models import Character, Lesson


class CurriculumTests(TestCase):
    def setUp(self):
        Character.objects.create(name='Emma', role='guide', personality='friendly')

    def test_seed_creates_episodes_through_b1(self):
        seed_curriculum()
        titles = list(
            Lesson.objects.filter(is_published=True)
            .order_by('unit__level', 'unit__order', 'order')
            .values_list('title', flat=True)
        )
        self.assertIn('Coffee in London', titles)
        self.assertIn('First Day at Work', titles)
        self.assertIn('Quick Team Update', titles)
        self.assertGreaterEqual(len(titles), 5)

    def test_curriculum_has_b1_unit(self):
        levels = {block['unit']['level'] for block in CURRICULUM}
        self.assertIn('b1', levels)
