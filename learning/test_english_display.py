from django.test import SimpleTestCase

from learning.english_display import (
    display_word_fields,
    format_english_text,
    format_headword,
    format_translation_display,
)


class EnglishDisplayTests(SimpleTestCase):
    def test_proper_noun_headword(self):
        self.assertEqual(format_headword('britain'), 'Britain')
        self.assertEqual(format_headword('london'), 'London')

    def test_sentence_and_example(self):
        disp = display_word_fields(
            english='britain',
            translation='британия',
            example='i live in britain.',
            part_of_speech='proper noun',
        )
        self.assertEqual(disp['english'], 'Britain')
        self.assertEqual(disp['translation'], 'Британия')
        self.assertEqual(disp['example'], 'I live in Britain.')

    def test_always_cap_in_sentence(self):
        self.assertEqual(
            format_english_text('i speak english in london.'),
            'I speak English in London.',
        )

    def test_common_word_unchanged(self):
        self.assertEqual(format_headword('please'), 'please')
        self.assertEqual(format_translation_display('пожалуйста', english='please'), 'пожалуйста')
