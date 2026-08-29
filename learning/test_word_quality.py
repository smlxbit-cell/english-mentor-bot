from django.test import SimpleTestCase

from learning.english_display import display_word_fields, format_headword
from learning.word_bank.word_quality import is_acceptable_headword


class WordQualityTests(SimpleTestCase):
    def test_rejects_two_letter_abbreviations(self):
        self.assertFalse(is_acceptable_headword('ab', 'пресс'))
        self.assertFalse(is_acceptable_headword('ac', 'переменный'))

    def test_allows_ok_tv(self):
        self.assertTrue(is_acceptable_headword('ok', 'хорошо'))
        self.assertTrue(is_acceptable_headword('tv', 'телевизор'))

    def test_allows_normal_words(self):
        self.assertTrue(is_acceptable_headword('academy', 'академия'))

    def test_afghanistan_capitalization(self):
        disp = display_word_fields(
            english='afghanistan',
            translation='афганистан',
            part_of_speech='',
        )
        self.assertEqual(disp['english'], 'Afghanistan')
        self.assertEqual(disp['translation'], 'Афганистан')
        self.assertEqual(format_headword('afghanistan'), 'Afghanistan')
