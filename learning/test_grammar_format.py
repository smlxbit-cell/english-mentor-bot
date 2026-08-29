from django.test import SimpleTestCase

from learning.grammar.format import format_rule_detail_html, grammar_speak_text


class GrammarFormatTests(SimpleTestCase):
    _RULE = {
        'level': 'a2',
        'topic': 'Отель',
        'title': 'Заселение в отель',
        'summary_ru': 'На ресепшене: check in и бронь на имя.',
        'table': {
            'headers': ['Ситуация', 'Фраза', 'Перевод'],
            'rows': [
                ['Заселение', "I'd like to check in, please.", 'Я бы хотел заселиться.'],
            ],
        },
        'examples': [
            {'en': 'What time is breakfast?', 'ru': 'Во сколько завтрак?'},
        ],
        'tip_ru': 'Under + фамилия = «на имя …».',
    }

    def test_compact_hides_table_when_card_present(self):
        html = format_rule_detail_html(self._RULE, has_card=True)
        self.assertNotIn('📋', html)
        self.assertNotIn('Таблица', html)
        self.assertNotIn('Заселение в отель', html)
        self.assertNotIn('💡', html)
        self.assertIn('check in', html)

    def test_full_shows_table_without_card(self):
        html = format_rule_detail_html(self._RULE, has_card=False)
        self.assertIn('📋', html)
        self.assertIn('check in', html)

    def test_speak_text_table_order_no_extras(self):
        rule = {
            'table': {
                'headers': ['Ситуация', 'Фраза', 'Перевод'],
                'rows': [
                    ['Нейтрально', 'Hello!', 'Здравствуй!'],
                    ['Друзья', 'Hi!', 'Привет!'],
                    ['Утро', 'Good morning!', 'Доброе утро!'],
                    ['Вечер', 'Good evening!', 'Добрый вечер!'],
                ],
            },
            'tip_ru': 'На «How are you?» часто отвечают «Good, thanks!» — не нужен длинный ответ.',
            'examples': [{'en': 'Hi! Nice to meet you.', 'ru': '…'}],
        }
        speak = grammar_speak_text(rule)
        self.assertEqual(
            speak,
            'Hello!. Hi!. Good morning!. Good evening!. How are you?. Good, thanks!',
        )
        self.assertNotIn('Nice to meet you', speak or '')

    def test_speak_text_uses_example_column_not_label(self):
        rule = {
            'table': {
                'headers': ['Фраза', 'Пример', 'Перевод'],
                'rows': [
                    ['Goodbye', 'Goodbye! Have a nice day.', 'До свидания!'],
                ],
            },
            'tip_ru': '',
        }
        speak = grammar_speak_text(rule)
        self.assertEqual(speak, 'Goodbye! Have a nice day.')
