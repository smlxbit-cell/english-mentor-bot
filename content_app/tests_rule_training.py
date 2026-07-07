"""Tests for rule training exercise builder."""

from django.test import TestCase

from content_app.rule_training import build_rule_training_exercises


class RuleTrainingTests(TestCase):
    def test_builds_up_to_four_exercises(self):
        rule = {
            'key': 'polite-requests',
            'title': 'Вежливые просьбы',
            'examples': [
                {'en': 'I would like a coffee, please.', 'ru': 'Я бы хотел кофе.'},
                {'en': 'Can I have the menu, please?', 'ru': 'Можно меню?'},
            ],
            'table': {
                'headers': ['Форма', 'Пример'],
                'rows': [['I would like…', 'I would like tea.']],
            },
        }
        exercises = build_rule_training_exercises(rule)
        self.assertGreaterEqual(len(exercises), 3)
        self.assertLessEqual(len(exercises), 4)
        types = {ex['exercise_type'] for ex in exercises}
        self.assertIn('multiple_choice', types)
        self.assertIn('fill_gap', types)
