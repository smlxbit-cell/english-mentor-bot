"""Tests for per-level word quotas."""

from django.test import SimpleTestCase

from learning.word_bank.level_quotas import LEVEL_TARGETS, apply_level_quotas


class LevelQuotaTests(SimpleTestCase):
    def test_a1_quota_keeps_curated_first(self):
        rows = {
            'remote': {
                'english': 'zebra',
                'cefr_level': 'a1',
                'topics': ['remote'],
                'kelly_rank': 999,
                'example': '',
                'example_ru': '',
            },
            'curated': {
                'english': 'hello',
                'cefr_level': 'a1',
                'topics': ['greetings'],
                'example': 'Say hello to the teacher.',
                'example_ru': 'Поздоровайся с учителем.',
            },
        }
        for i in range(510):
            rows[f'w{i}'] = {
                'english': f'word{i}',
                'cefr_level': 'a1',
                'topics': ['remote'],
                'kelly_rank': i,
                'example': '',
                'example_ru': '',
            }
        kept, dropped = apply_level_quotas(rows, levels=('a1',), kelly_ranks={})
        self.assertEqual(len([r for r in kept.values() if r['cefr_level'] == 'a1']), LEVEL_TARGETS['a1'])
        self.assertIn('curated', kept)
        self.assertIn('remote', dropped)
