"""Tests for the economical checker, speaking scorer and grammar KB (no tokens)."""

from asgiref.sync import async_to_sync
from django.test import TestCase

from ai_app.services import (
    AnswerChecker,
    explain_grammar,
    extract_best_word_match,
    normalize,
    score_speaking,
    score_word_review,
)


class CheckerDeterministicTests(TestCase):
    def setUp(self):
        self.checker = AnswerChecker()

    def _check(self, **kwargs):
        return async_to_sync(self.checker.check)(**kwargs)

    def test_multiple_choice_correct(self):
        res = self._check(
            exercise_type='multiple_choice',
            user_answer='No, thank you.',
            correct=['No, thank you.'],
        )
        self.assertTrue(res.is_correct)
        self.assertEqual(res.method, 'options')
        self.assertFalse(res.used_ai)

    def test_multiple_choice_incorrect(self):
        res = self._check(
            exercise_type='multiple_choice',
            user_answer='No.',
            correct=['No, thank you.'],
        )
        self.assertFalse(res.is_correct)

    def test_fill_gap_case_insensitive(self):
        res = self._check(
            exercise_type='fill_gap',
            user_answer='Would',
            correct=['would'],
        )
        self.assertTrue(res.is_correct)

    def test_word_order(self):
        res = self._check(
            exercise_type='word_order',
            user_answer='Where are you from',
            correct=['where are you from'],
        )
        self.assertTrue(res.is_correct)

    def test_keyword_coverage(self):
        res = self._check(
            exercise_type='translation_ru_en',
            user_answer='I was at home yesterday',
            keywords=['was', 'home', 'yesterday'],
        )
        self.assertTrue(res.is_correct)

    def test_empty_answer(self):
        res = self._check(
            exercise_type='fill_gap', user_answer='', correct=['would'],
        )
        self.assertFalse(res.is_correct)
        self.assertEqual(res.method, 'empty')


    def test_fill_gap_from_phrase(self):
        res = self._check(
            exercise_type='fill_gap',
            user_answer="it's would",
            correct=['would'],
        )
        self.assertTrue(res.is_correct)


class SpeakingScoreTests(TestCase):
    def test_close_match_is_correct(self):
        res = score_speaking('a cup of coffee please', 'A cup of coffee, please.')
        self.assertTrue(res.is_correct)

    def test_empty_transcript_is_lenient(self):
        res = score_speaking('', 'A cup of coffee, please.')
        self.assertTrue(res.is_correct)


class GrammarKBTests(TestCase):
    def test_known_topic_returns_explanation(self):
        self.assertIsNotNone(explain_grammar('расскажи про present simple'))
        self.assertIn('Present Simple', explain_grammar('present simple'))

    def test_unknown_topic_returns_none(self):
        self.assertIsNone(explain_grammar('asdfghjkl qwerty'))


class WordReviewTests(TestCase):
    def test_extract_from_phrase(self):
        word, ratio = extract_best_word_match("It's coffee", 'coffee')
        self.assertEqual(word, 'coffee')
        self.assertGreaterEqual(ratio, 0.99)

    def test_extract_would_from_sentence(self):
        word, ratio = extract_best_word_match('I would like', 'would')
        self.assertEqual(word, 'would')
        self.assertGreaterEqual(ratio, 0.99)

    def test_score_word_review_ok(self):
        ok, guess, _ = score_word_review('coffee please', 'coffee')
        self.assertTrue(ok)
        self.assertEqual(guess, 'coffee')


class NormalizeTests(TestCase):
    def test_strips_punctuation_and_case(self):
        self.assertEqual(normalize('  Would!! '), 'would')
