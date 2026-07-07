"""Level variant resolution tests."""

from django.test import TestCase

from content_app.level_variants import apply_level_variants


class LevelVariantTests(TestCase):
    def test_merges_best_variant_for_b2(self):
        steps = [{
            'step_type': 'exercise',
            'content': {
                'exercise_type': 'multiple_choice',
                'level_variants': {
                    'a2': {'options': ['A'], 'correct': ['A']},
                    'b2': {'options': ['B'], 'correct': ['B']},
                },
                'options': ['fallback'],
                'correct': ['fallback'],
            },
        }]
        out = apply_level_variants(steps, 'B2')
        self.assertEqual(out[0]['content']['correct'], ['B'])

    def test_skips_min_level_step(self):
        steps = [
            {'step_type': 'story', 'content': {'min_level': 'b1', 'text': 'hard'}},
            {'step_type': 'story', 'content': {}},
        ]
        out = apply_level_variants(steps, 'a2')
        self.assertEqual(len(out), 1)

    def test_a2_gets_a2_variant_not_b2(self):
        steps = [{
            'content': {
                'level_variants': {
                    'a2': {'correct': ['easy']},
                    'b2': {'correct': ['hard']},
                },
                'correct': ['fallback'],
            },
        }]
        out = apply_level_variants(steps, 'a2')
        self.assertEqual(out[0]['content']['correct'], ['easy'])
