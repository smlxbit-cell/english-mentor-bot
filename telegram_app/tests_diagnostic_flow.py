"""Diagnostic flow tests."""

from django.test import TestCase

from telegram_app.bot import diagnostic_flow as diag_flow


class DiagnosticFlowTests(TestCase):
    def _group(self):
        return {
            'a1': [
                {'id': 1, 'skill': 'grammar', 'item_type': 'multiple_choice'},
                {'id': 2, 'skill': 'listening', 'item_type': 'listening'},
            ],
            'a2': [
                {'id': 3, 'skill': 'vocabulary', 'item_type': 'multiple_choice'},
                {'id': 4, 'skill': 'listening', 'item_type': 'listening'},
                {'id': 5, 'skill': 'speaking', 'item_type': 'speaking'},
            ],
        }

    def test_prefer_skill_picks_listening(self):
        item = diag_flow.pick_item(
            self._group(), set(), (0, 2), 1, prefer_skill='listening',
        )
        self.assertEqual(item['skill'], 'listening')

    def test_prefer_skill_for_question_rotation(self):
        self.assertEqual(diag_flow.prefer_skill_for_question(3), 'listening')
        self.assertEqual(diag_flow.prefer_skill_for_question(5), 'speaking')
        self.assertIsNone(diag_flow.prefer_skill_for_question(2))

    def test_prefer_skill_stops_after_two_listening(self):
        self.assertIsNone(
            diag_flow.prefer_skill_for_question(6, listening_count=2),
        )
