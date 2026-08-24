"""Tests for usage example enrichment."""

from django.test import SimpleTestCase

from learning.word_bank.example_enrich import enrich_row_examples, is_valid_context_example


class ExampleEnrichTests(SimpleTestCase):
    def test_valid_context_example(self):
        row = {
            'english': 'apparent',
            'translation': 'очевидный',
            'example': 'It was apparent that she was upset.',
            'example_ru': 'Было очевидно, что она расстроена.',
        }
        self.assertTrue(is_valid_context_example(row))

    def test_rejects_i_like_template(self):
        row = {
            'english': 'apparent',
            'translation': 'очевидный',
            'example': 'I like apparent.',
            'example_ru': 'Мне нравится видимый.',
        }
        self.assertFalse(is_valid_context_example(row))

    def test_override_replaces_bad_example(self):
        row = {
            'english': 'apparent',
            'translation': 'очевидный',
            'example': 'I like apparent.',
            'example_ru': 'Мне нравится видимый.',
        }
        enriched = enrich_row_examples(row)
        self.assertIn('apparent', enriched['example'].lower())
        self.assertTrue(enriched['example_ru'])
        self.assertNotRegex(enriched['example'], r'^I like ')
