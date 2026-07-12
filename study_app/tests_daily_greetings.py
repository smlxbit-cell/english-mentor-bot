"""Greeting and reminder copy tests."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from study_app.daily_facts import (
    pick_plan_greeting,
    pick_reminder_lines,
    time_greeting_ru,
)


class DailyGreetingsTests(TestCase):
    def test_time_greeting_morning(self):
        self.assertEqual(time_greeting_ru(8), 'доброе утро')

    def test_time_greeting_afternoon(self):
        self.assertEqual(time_greeting_ru(14), 'добрый день')

    def test_time_greeting_evening(self):
        self.assertEqual(time_greeting_ru(19), 'добрый вечер')

    def test_time_greeting_night(self):
        self.assertEqual(time_greeting_ru(1), 'привет')

    def test_plan_greeting_uses_time_of_day(self):
        morning = datetime(2026, 7, 12, 9, 0, tzinfo=ZoneInfo('Europe/Moscow'))
        evening = datetime(2026, 7, 12, 20, 0, tzinfo=ZoneInfo('Europe/Moscow'))
        day = date(2026, 7, 12)
        am = pick_plan_greeting('Мария', 1, day, now=morning)
        pm = pick_plan_greeting('Мария', 1, day, now=evening)
        self.assertIn('доброе утро', am)
        self.assertIn('добрый вечер', pm)
        self.assertNotIn('доброе утро', pm)

    def test_reminder_lines_vary(self):
        day = date(2026, 7, 12)
        a = pick_reminder_lines('Мария', 1, day, 10)
        b = pick_reminder_lines('Мария', 2, day, 10)
        self.assertNotEqual('\n'.join(a), '\n'.join(b))

    def test_reminder_includes_quote(self):
        lines = pick_reminder_lines('Мария', 5, date(2026, 7, 12), 10)
        self.assertTrue(any('💬' in ln for ln in lines))
