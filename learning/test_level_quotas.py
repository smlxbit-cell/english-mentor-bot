"""Tests for per-level word quotas."""

from django.test import SimpleTestCase

from learning.word_bank.level_quotas import LEVEL_TARGETS, apply_level_quotas, quota_levels_for_requested


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

    def test_quota_levels_for_requested_includes_lower_bands(self):
        self.assertEqual(quota_levels_for_requested(('a2',)), ('a1', 'a2'))

    def test_native_levels_do_not_cross_promote(self):
        rows = {
            f'c1_{i}': {
                'english': f'advanced{i}',
                'cefr_level': 'c1',
                'topics': ['remote'],
                'kelly_rank': i,
                'example': '',
                'example_ru': '',
            }
            for i in range(120)
        }
        rows.update({
            f'b2_{i}': {
                'english': f'b2word{i}',
                'cefr_level': 'b2',
                'topics': ['remote'],
                'kelly_rank': i,
                'example': '',
                'example_ru': '',
            }
            for i in range(80)
        })
        kept, _ = apply_level_quotas(rows, levels=('b2', 'c1'), kelly_ranks={})
        c1_kept = [r for r in kept.values() if r['cefr_level'] == 'c1']
        b2_kept = [r for r in kept.values() if r['cefr_level'] == 'b2']
        self.assertEqual(len(c1_kept), 120)
        self.assertEqual(len(b2_kept), 80)

    def test_total_targets_about_five_thousand(self):
        self.assertEqual(sum(LEVEL_TARGETS.values()), 5000)
