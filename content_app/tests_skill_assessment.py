"""Tests for the in-depth per-skill assessment bank and logic."""

from django.test import TestCase

from content_app import skill_assessment as sa


class SkillAssessmentTests(TestCase):
    def test_build_test_covers_all_skills(self):
        queue = sa.build_test('b1')
        skills = {it['skill'] for it in queue}
        self.assertEqual(skills, set(sa.SKILLS))
        # Text skills give PER_TEXT_SKILL each, speaking gives PER_SPEAKING.
        counts = {}
        for it in queue:
            counts[it['skill']] = counts.get(it['skill'], 0) + 1
        for text_skill in ('grammar', 'vocabulary', 'reading', 'listening', 'writing'):
            self.assertEqual(counts[text_skill], sa.PER_TEXT_SKILL)
        self.assertEqual(counts['speaking'], sa.PER_SPEAKING)

    def test_build_test_targets_user_level(self):
        # For an A1 user, the first grammar item should be at/near A1.
        queue = sa.build_test('a1')
        grammar = [it for it in queue if it['skill'] == 'grammar']
        self.assertIn(grammar[0]['level'], ('a1', 'a2'))

    def test_listening_items_hide_text_via_audio_field(self):
        queue = sa.build_test('b2')
        listening = [it for it in queue if it['skill'] == 'listening']
        for it in listening:
            self.assertTrue(it.get('audio_en'))

    def test_recommend_returns_weak_skills(self):
        scores = {
            'grammar': (4, 4),      # 100%
            'vocabulary': (3, 4),   # 75%
            'listening': (1, 4),    # 25% -> weak
            'writing': (2, 4),      # 50% -> weak
            'reading': (4, 4),      # 100%
            'speaking': (0, 2),     # 0% -> weak
        }
        weak = sa.recommend(scores)
        self.assertLessEqual(len(weak), 3)
        self.assertEqual(weak[0], 'speaking')  # worst first
        self.assertIn('listening', weak)

    def test_recommend_when_all_strong_picks_lowest(self):
        scores = {'grammar': (4, 4), 'vocabulary': (3, 4)}
        weak = sa.recommend(scores)
        self.assertEqual(weak, ['vocabulary'])

    def test_score_summary_formats_percentages(self):
        text = sa.score_summary({'grammar': (2, 4)})
        self.assertIn('Грамматика', text)
        self.assertIn('50%', text)
