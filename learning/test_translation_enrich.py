"""Tests for multi-sense translation enrichment."""

from django.test import SimpleTestCase

from learning.word_bank.translation_enrich import (
    enrich_translation,
    extract_freedict_senses,
    merge_translation_parts,
    sanitize_translation_for_display,
    split_translation_parts,
)


class TranslationEnrichTests(SimpleTestCase):
    def test_split_translation_parts(self):
        self.assertEqual(
            split_translation_parts('идти / ехать, идти'),
            ['идти', 'ехать'],
        )

    def test_chip_override(self):
        text = (
            'noun чипс A small piece broken from a larger piece of solid material. '
            'лучина обломок осколок (games, gambling) фишка '
            '(electronics) чип микросхема'
        )
        result = enrich_translation('chip', 'обломок, осколок', freedict_text=text)
        self.assertEqual(result, 'чип, чипс, обломок, фишка')

    def test_rich_primary_not_overloaded(self):
        primary = 'бежать, бег, управлять, работать, функционировать'
        result = enrich_translation('run', primary, freedict_text='verb бежать убегать')
        self.assertEqual(result, primary)

    def test_bank_keeps_primary_when_freedict_is_other_pos(self):
        result = enrich_translation(
            'bank',
            'банк',
            freedict_text='verb накреняться класть в банк',
            part_of_speech='noun',
        )
        self.assertEqual(result, 'банк, берег')

    def test_extract_freedict_senses_from_tagged_noun(self):
        text = (
            'noun весна A season of the year. '
            'пружина An elastic mechanical part. '
            '(countable) источник The source from which something springs.'
        )
        senses = extract_freedict_senses(text, max_senses=3, part_of_speech='noun')
        self.assertEqual(senses, ['весна', 'пружина', 'источник'])

    def test_merge_promotes_loanword(self):
        merged = merge_translation_parts('disk', 'дискета', 'диск, накопитель')
        self.assertTrue(merged.startswith('диск'))

    def test_sanitize_aggressive_freedict_blob(self):
        blob = (
            '/ əˈɡɹɛs.ɪv / adjective Characterized by aggression; highly combative; '
            'prone to behave in a way that involves attacking or arguing. '
            '(pathology, of a tumour or disease) That spreads quickly; virulent. '
            'агрессивный воинственный агрессивный'
        )
        result = sanitize_translation_for_display(
            blob, english='aggressive', part_of_speech='adjective',
        )
        self.assertIn('агрессивный', result)
        self.assertNotIn('Characterized', result)
        self.assertNotIn('/', result)
