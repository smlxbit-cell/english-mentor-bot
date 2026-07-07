"""Story placement for high-level learners."""

from django.test import TestCase

from content_app.curriculum import seed_curriculum
from content_app.models import Character, Lesson
from study_app.models import LessonProgress
from study_app.services.daily_plan import get_next_episode_lesson
from study_app.services.episode_routing import apply_story_placement
from users_app.models import UserProfile


class EpisodeRoutingTests(TestCase):
    def setUp(self):
        Character.objects.create(name='Emma', role='guide')
        seed_curriculum()
        self.profile = UserProfile.objects.create(
            telegram_id=9001,
            first_name='B2User',
            cefr_level='B2',
            diagnostic_completed=True,
            learning_goal='work',
            profession='it',
            study_schedule_set=True,
        )

    def test_b2_skips_a1_and_starts_at_work(self):
        title = apply_story_placement(self.profile)
        self.assertEqual(title, 'First Day at Work')
        nxt = get_next_episode_lesson(self.profile)
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.title, 'First Day at Work')
        skipped = LessonProgress.objects.filter(
            user=self.profile,
            status=LessonProgress.Status.SKIPPED,
        ).count()
        self.assertGreater(skipped, 0)
        coffee = Lesson.objects.get(title='Coffee in London')
        self.assertTrue(
            LessonProgress.objects.filter(
                user=self.profile,
                lesson=coffee,
                status=LessonProgress.Status.SKIPPED,
            ).exists()
        )
