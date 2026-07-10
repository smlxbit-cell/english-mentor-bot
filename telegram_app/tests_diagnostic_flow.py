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
            diag_flow.prefer_skill_for_question(7, listening_count=2),
        )
        self.assertEqual(diag_flow.prefer_skill_for_question(7, listening_count=1), 'listening')

    def test_prompt_key_dedupes_same_sentence(self):
        group = {
            'b2': [
                {'id': 1, 'skill': 'grammar', 'item_type': 'multiple_choice',
                 'prompt': 'She suggested ___ earlier.'},
                {'id': 2, 'skill': 'grammar', 'item_type': 'fill_gap',
                 'prompt': '«Она предложила уйти»\n\nShe suggested ___ earlier.'},
                {'id': 3, 'skill': 'vocabulary', 'item_type': 'multiple_choice',
                 'prompt': 'Different question ___ here.'},
            ],
        }
        asked = {1}
        prompts = {diag_flow.prompt_key(group['b2'][0])}
        item = diag_flow.pick_item(group, asked, (3, 3), 3, asked_prompts=prompts)
        self.assertEqual(item['id'], 3)

    def test_explanation_detail_despite_deep(self):
        item = {
            'prompt': 'Despite ___, we went for a walk.',
            'options': ['the rain', 'rainy', 'raining'],
            'correct': ['the rain'],
            'explanation_ru': 'short',
        }
        text = diag_flow.explanation_detail(item, 'the rain', was_correct=True)
        self.assertIn('the rain', text)
        self.assertIn('rainy', text)
        self.assertIn('артикль', text.lower())

    def test_explanation_detail_correct(self):
        item = {
            'correct': ['had'],
            'explanation_ru': 'Нереальное сейчас: <b>If I had</b> more time…',
            'prompt': 'If I ___ more time, I would travel.',
            'options': ['had', 'have', 'has'],
        }
        text = diag_flow.explanation_detail(item, 'had', was_correct=True)
        self.assertIn('✅', text)
        self.assertIn('второе условное', text.lower())

    def test_b2_primary_strong_stays_b2_without_challenge(self):
        diag = {
            'claimed': 'b2', 'claimed_idx': 3,
            'band': (2, 3, 3), 'correct': 9, 'count': 10, 'level_idx': 3,
        }
        self.assertEqual(diag_flow.confirmed_primary_level(diag), 3)
        self.assertEqual(diag_flow.finalize_level(diag), 'b2')

    def test_b2_primary_plus_challenge_pass_gives_c1(self):
        diag = {
            'claimed': 'b2', 'claimed_idx': 3, 'confirmed_idx': 3,
            'band': (4, 4), 'correct': 10, 'count': 10, 'level_idx': 4,
            'phase': 'challenge_done', 'challenge_correct': 3,
        }
        self.assertEqual(diag_flow.finalize_level(diag), 'c1')

    def test_b2_primary_plus_failed_challenge_stays_b2(self):
        diag = {
            'claimed': 'b2', 'claimed_idx': 3, 'confirmed_idx': 3,
            'band': (4, 4), 'correct': 10, 'count': 10, 'level_idx': 4,
            'phase': 'challenge_done', 'challenge_correct': 1,
        }
        self.assertEqual(diag_flow.finalize_level(diag), 'b2')

    def test_a1_strong_offers_a2_challenge(self):
        diag = {
            'claimed': 'a1', 'claimed_idx': 0,
            'band': (0, 1, 0), 'correct': 10, 'count': 10, 'level_idx': 1,
            'phase': 'primary_done',
        }
        self.assertTrue(diag_flow.should_offer_challenge(diag))
        self.assertEqual(diag_flow.confirmed_primary_level(diag), 0)
