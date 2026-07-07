from django.test import TestCase

from telegram_app.bot.handlers import _english_text_for_tts, _speak_text_for_step


class LessonTTSTests(TestCase):
    def test_extract_english_from_hook_step(self):
        text = (
            '☕️ <b>Эпизод 1. Coffee in London</b>\n\n'
            'Лондон, утро.\n'
            '🇬🇧 Hi! Are you new here?\n'
            '(Привет! Ты здесь новенький?)\n\n'
            'Это Эмма.'
        )
        self.assertEqual(_english_text_for_tts(text), 'Hi! Are you new here?')

    def test_extract_multiple_english_lines(self):
        text = (
            'Эмма шепчёт:\n'
            '🇬🇧 Just be polite and smile — the rest is easy.\n'
            '(Будь вежлив.)\n\n'
            'Том говорит:\n'
            '🇬🇧 Good morning! What can I get you?\n'
            '(Доброе утро!)'
        )
        self.assertEqual(
            _english_text_for_tts(text),
            'Just be polite and smile — the rest is easy. '
            'Good morning! What can I get you?',
        )

    def test_speak_text_for_story_hook_without_speak_en(self):
        step = {
            'step_type': 'hook',
            'text': (
                'Лондон, утро.\n'
                '🇬🇧 Hi! Are you new here?\n'
                '(Привет!)'
            ),
            'content': {},
        }
        self.assertEqual(_speak_text_for_step(step), 'Hi! Are you new here?')

    def test_tts_spirit_bilingual_reply(self):
        """Spirit self-intro: voice all 🇬🇧 English lines, no duplicate on Ещё можно сказать."""
        text = (
            '🇷🇺 <b>По-русски:</b>\n'
            'Я — Спирит, маленький светящийся дух языка.\n\n'
            '🇬🇧 <b>English:</b> I am Spirit — «Я — Спирит»\n'
            'English: a small glowing language spirit — «маленький светящийся дух языка»\n'
            'English: I can explain words, phrases, and grammar — «Я могу объяснять слова»\n\n'
            '👍 Хорошая мысль!\n'
            '<b>Грамматика:</b> ✅ Грамматически верно.\n'
            '<b>Ещё можно сказать:</b> «I am here to help you learn English» — '
            '«Я здесь, чтобы помочь тебе учить английский».'
        )
        tts = _english_text_for_tts(text)
        self.assertIn('I am Spirit', tts)
        self.assertIn('small glowing language spirit', tts)
        self.assertIn('explain words', tts)
        self.assertIn('help you learn English', tts)
        self.assertEqual(tts.count('help you learn English'), 1)

    def test_tts_voice_mode_heard_quote(self):
        text = (
            '🇷🇺 <b>По-русски:</b>\n'
            'Услышал: «Tell me more detail, what you can do» — «Расскажи подробнее»\n'
            '<b>Ещё можно сказать:</b> «Could you tell me more about your features» — «…»'
        )
        tts = _english_text_for_tts(text)
        self.assertIn('Tell me more detail', tts)
        self.assertIn('Could you tell me more', tts)

    def test_tts_no_duplicate_on_eshe_mozhno_skazat(self):
        """Услышал + Ещё можно сказать: each English phrase once, no repeat at end."""
        text = (
            '🇷🇺 <b>По-русски:</b>\n'
            'Услышал: «Could you help me write my thoughts and day in English?» — '
            '«Не мог бы ты помочь мне написать мои мысли и день на английском?»\n'
            '👍 Хорошая мысль!\n'
            '<b>Грамматика:</b> ✅ Грамматически верно.\n'
            '<b>Ещё можно сказать:</b> «Can you assist me in expressing my thoughts '
            'and day in English?» — «Можешь помочь мне выразить мои мысли и день на английском?»'
        )
        tts = _english_text_for_tts(text)
        self.assertIn('Could you help me write', tts)
        self.assertIn('Can you assist me', tts)
        self.assertEqual(tts.lower().count('can you assist me'), 1)

    def test_speak_text_prefers_explicit_speak_en(self):
        step = {
            'step_type': 'story',
            'text': '🇬🇧 Other phrase.',
            'content': {'speak_en': 'I would like a coffee, please.'},
        }
        self.assertEqual(_speak_text_for_step(step), 'I would like a coffee, please.')
