"""Roadmap / motivation map tests."""

from django.test import TestCase

from content_app.models import GrammarRule, Lesson
from gamification_app.models import UserStats
from study_app.services.roadmap import build_roadmap, format_roadmap_message
from users_app.models import UserProfile


class RoadmapTests(TestCase):
    def setUp(self):
        self.profile = UserProfile.objects.create(
            telegram_id=2001,
            first_name='Road',
            cefr_level='A1',
            diagnostic_completed=True,
            daily_minutes=30,
            study_days_per_week=5,
            study_schedule_set=True,
        )
        UserStats.objects.create(user=self.profile, xp_total=120, current_streak=3)
        self.l1 = Lesson.objects.create(
            title='Ep 1', subtitle='London', level='a1', order=1,
            is_published=True, is_trial=True, estimated_minutes=10,
        )
        Lesson.objects.create(
            title='Ep 2', subtitle='Manchester', level='a1', order=2,
            is_published=True, is_trial=True, estimated_minutes=12,
        )
        for i in range(3):
            GrammarRule.objects.create(
                key=f'a1-rule-{i}',
                title=f'Rule {i}',
                topic='Basics',
                level='a1',
                order=i,
                is_published=True,
            )

    def test_roadmap_shows_eta_range(self):
        data = build_roadmap(self.profile)
        self.assertEqual(data['current_level'], 'A1')
        self.assertEqual(data['goal_level'], 'A2')
        self.assertGreaterEqual(data['lessons_total'], 2)
        self.assertIsNotNone(data['goal_weeks_low'])
        self.assertGreater(data['goal_months_high'], data['goal_months_low'])

    def test_roadmap_with_target_c1(self):
        self.profile.cefr_level = 'B2'
        self.profile.target_cefr_level = 'C1'
        self.profile.save()
        data = build_roadmap(self.profile)
        self.assertEqual(data['goal_level'], 'C1')
        self.assertIn('C1', data['journey_map'])
        self.assertGreater(data['goal_months_low'], 0)

    def test_format_includes_map_and_disclaimer(self):
        data = build_roadmap(self.profile)
        text = format_roadmap_message(data)
        self.assertIn('Карта пути', text)
        self.assertIn('A1', text)
        self.assertIn('A2', text)
        self.assertIn('месяц', text)
        self.assertIn('не гарантия', text)

    def test_progress_increases_when_lesson_completed(self):
        from study_app.models import LessonProgress

        LessonProgress.objects.create(
            user=self.profile,
            lesson=self.l1,
            status=LessonProgress.Status.COMPLETED,
        )
        data = build_roadmap(self.profile)
        self.assertEqual(data['lessons_done'], 1)
        self.assertGreater(data['step_percent'], 0)
