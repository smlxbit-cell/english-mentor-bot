"""Funnel + adaptive + SRS tests for the bot DB layer.

Covers the diagnostic -> trial -> paywall funnel, adaptive lesson ranking,
and vocabulary spaced-repetition wiring.

The db.* helpers are wrapped with @sync_to_async; in tests we call the raw
synchronous function via `.func` so everything runs inside the test's
transaction (no event loop / cross-thread visibility issues).
"""

from django.test import TestCase
from django.utils import timezone

from billing_app.models import SubscriptionPlan
from content_app.models import Character, Lesson, LessonStep
from gamification_app.models import UserStats
from telegram_app.bot import db
from users_app.models import Interest, UserProfile


def sync(wrapped):
    """Return the raw sync function behind a @sync_to_async wrapper."""
    return getattr(wrapped, 'func', wrapped)


class BotFunnelTests(TestCase):
    def setUp(self):
        SubscriptionPlan.objects.create(
            code='monthly', name='Месячный', price_rub=390, duration_days=30,
        )
        self.emma = Character.objects.create(name='Emma')
        self.profile = UserProfile.objects.create(
            telegram_id=42, first_name='Test', cefr_level='A1',
            diagnostic_completed=True, weak_skills=['grammar'],
        )
        UserStats.objects.create(user=self.profile)

        self.trial = Lesson.objects.create(
            title='Trial A1', level='a1', order=1, is_trial=True,
            is_published=True, xp_reward=50, character=self.emma,
            tags=['travel'],
        )
        LessonStep.objects.create(
            lesson=self.trial, order=1, step_type='vocabulary', skill='vocabulary',
            content={'words': [{'en': 'cat', 'ru': 'кот', 'example': 'A cat sleeps.'}]},
        )
        LessonStep.objects.create(
            lesson=self.trial, order=2, step_type='exercise', skill='grammar',
            content={'exercise_type': 'multiple_choice',
                     'options': ['a', 'b'], 'correct': ['a']},
        )
        self.paid = Lesson.objects.create(
            title='Paid A1', level='a1', order=2, is_trial=False,
            is_published=True, xp_reward=50,
        )

    def test_available_lessons_marks_recommended(self):
        data = sync(db.get_available_lessons)(self.profile.id)
        self.assertEqual(data['level'], 'a1')
        self.assertGreaterEqual(len(data['lessons']), 2)
        recommended = [l for l in data['lessons'] if l.get('recommended')]
        self.assertEqual(len(recommended), 1)
        self.assertFalse(recommended[0]['completed'])

    def test_full_trial_opens_everything_then_paywall_after_expiry(self):
        # During the 2-day full trial, all lessons (incl. non-trial) are open.
        gate = sync(db.can_start_lesson)(self.profile.id, self.trial.id)
        self.assertTrue(gate['allowed'])
        gate2 = sync(db.can_start_lesson)(self.profile.id, self.paid.id)
        self.assertTrue(gate2['allowed'])

        # After the trial window expires, non-premium users hit the paywall.
        from datetime import timedelta
        self.profile.refresh_from_db()
        self.profile.trial_started_at = timezone.now() - timedelta(days=5)
        self.profile.save()
        gate3 = sync(db.can_start_lesson)(self.profile.id, self.paid.id)
        self.assertFalse(gate3['allowed'])

    def test_complete_lesson_flags_paywall_after_trial_expiry(self):
        from datetime import timedelta
        # Move the trial start into the past so the trial is over.
        self.profile.trial_started_at = timezone.now() - timedelta(days=5)
        self.profile.save()
        sync(db.start_or_resume_lesson)(self.profile.id, self.trial.id)
        summary = sync(db.complete_lesson)(self.profile.id, self.trial.id)
        self.assertTrue(summary['need_paywall'])
        self.assertGreaterEqual(summary['xp_earned'], 50)


class AdaptiveInterestTests(TestCase):
    def setUp(self):
        self.profile = UserProfile.objects.create(
            telegram_id=7, first_name='Ada', cefr_level='A2',
            diagnostic_completed=True, weak_skills=[],
        )
        UserStats.objects.create(user=self.profile)

    def test_toggle_interest_and_goal(self):
        interest = Interest.objects.create(name='Travel', slug='travel')
        ids = sync(db.toggle_interest)(self.profile.id, interest.id)
        self.assertIn(interest.id, ids)
        ids2 = sync(db.toggle_interest)(self.profile.id, interest.id)
        self.assertNotIn(interest.id, ids2)

        sync(db.set_learning_goal)(self.profile.id, 'work')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.learning_goal, 'work')


class VocabSRSTests(TestCase):
    def setUp(self):
        self.profile = UserProfile.objects.create(
            telegram_id=99, first_name='Voc', cefr_level='A1',
            diagnostic_completed=True,
        )
        UserStats.objects.create(user=self.profile)

    def test_save_words_and_review_schedule(self):
        words = [
            {'en': 'coffee', 'ru': 'кофе', 'example': 'I love coffee.'},
            {'en': 'tea', 'ru': 'чай', 'example': 'A cup of tea.'},
        ]
        added = sync(db.save_lesson_words)(self.profile.id, words)
        self.assertEqual(added, 2)

        due = sync(db.get_due_words)(self.profile.id)
        self.assertEqual(len(due), 2)

        word_id = due[0]['word_id']
        sync(db.record_word_review)(self.profile.id, word_id, True)

        from progress_app.models import UserWordProgress
        uwp = UserWordProgress.objects.get(user=self.profile, word_id=word_id)
        self.assertEqual(uwp.correct_count, 1)
        self.assertIsNotNone(uwp.next_review_at)
        self.assertGreater(uwp.next_review_at, timezone.now())
        due_after = sync(db.get_due_words)(self.profile.id)
        self.assertNotIn(word_id, [d['word_id'] for d in due_after])
