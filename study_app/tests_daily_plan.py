"""Daily plan v2 — weighted progress, warmup quiz, schedule sizing."""

from datetime import date

from django.test import TestCase

from content_app.models import Lesson
from study_app.services.daily_plan import (
    build_or_get_daily_plan,
    effective_daily_minutes,
    is_rest_day,
)
from study_app.warmup_quiz import build_quiz_for_fact
from users_app.models import UserProfile


class DailyPlanV2Tests(TestCase):
    def setUp(self):
        self.profile = UserProfile.objects.create(
            telegram_id=1001,
            first_name='Plan',
            cefr_level='A1',
            diagnostic_completed=True,
            learning_goal='travel',
            profession='it',
            daily_minutes=30,
            study_days_per_week=5,
            rest_weekday=6,
            study_schedule_set=True,
            onboarding_status='completed',
        )
        Lesson.objects.create(
            title='Trial ep',
            level='a1',
            order=1,
            is_trial=True,
            is_published=True,
            estimated_minutes=10,
        )

    def test_effective_daily_minutes_legacy_ten(self):
        self.profile.daily_minutes = 10
        self.profile.save()
        self.assertEqual(effective_daily_minutes(self.profile), 20)

    def test_warmup_quiz_has_one_correct(self):
        fact = {
            'kind': 'fact',
            'ru': 'Тест',
            'en': 'Test fact about English.',
        }
        quiz = build_quiz_for_fact(
            {'fact_ru': fact['ru'], 'fact_en': fact['en'], 'kind': 'fact'},
            user_id=1,
            day=date(2026, 7, 7),
        )
        self.assertEqual(len(quiz['options']), 4)
        self.assertEqual(quiz['correct_index'], quiz['options'].index(
            next(o for o in quiz['options'] if o == 'Test fact about English.')
        ))

    def test_plan_includes_listening_for_30_min(self):
        plan = build_or_get_daily_plan(self.profile, day=date(2026, 7, 8))
        self.assertIsNotNone(plan.get('listening'))
        self.assertGreater(plan.get('progress_minutes_total', 0), 10)
        self.assertIn('progress_percent', plan)

    def test_plan_20_min_no_listening(self):
        self.profile.daily_minutes = 20
        self.profile.save()
        plan = build_or_get_daily_plan(self.profile, day=date(2026, 7, 9))
        self.assertIsNone(plan.get('listening'))

    def test_rest_day_sunday(self):
        self.profile.rest_weekday = 6
        self.profile.save()
        sunday = date(2026, 7, 12)  # Sunday
        self.assertTrue(is_rest_day(self.profile, sunday))
        plan = build_or_get_daily_plan(self.profile, day=sunday)
        self.assertTrue(plan.get('is_rest_day'))
        self.assertIsNone(plan.get('episode'))
        self.assertIsNotNone(plan.get('warmup'))

    def test_warmup_block_has_quiz(self):
        plan = build_or_get_daily_plan(self.profile, day=date(2026, 7, 10))
        warmup = plan.get('warmup')
        self.assertIsNotNone(warmup)
        self.assertIsNotNone(warmup.get('quiz'))
        self.assertEqual(warmup.get('target_minutes'), 3)
