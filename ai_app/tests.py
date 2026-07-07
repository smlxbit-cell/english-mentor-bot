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


class BilingualSTTTests(TestCase):
    def test_split_cyrillic_phonetic_english_tail(self):
        from ai_app.speech.bilingual import merge_tutor_transcripts, split_cyrillic_mixed_transcript

        ru = 'Поговори сегодня со мной расскажи вот айл филин тудей'
        en = 'Pogovorii segodne se mnoi raskaji vot i ll fillin tutey'
        ru_part, en_part = split_cyrillic_mixed_transcript(ru)
        self.assertIn('Поговори', ru_part)
        self.assertNotIn('айл', ru_part)
        self.assertIn('feel', en_part.lower())
        self.assertIn('today', en_part.lower())

        merged = merge_tutor_transcripts(ru, en)
        self.assertIn('\n', merged)
        head, tail = merged.split('\n', 1)
        self.assertTrue(head.strip())
        self.assertNotIn('Pogovorii', tail)
        self.assertNotIn('segodne', tail.lower())

    def test_transliterated_russian_en_line_not_shown_raw(self):
        from ai_app.speech.bilingual import (
            is_meaningful_english_fragment,
            looks_like_transliterated_russian,
            tutor_transcript_label,
        )

        en = 'Pogovorii segodne se mnoi raskaji vot i ll fillin tutey'
        self.assertTrue(looks_like_transliterated_russian(en))
        label = tutor_transcript_label('Поговори сегодня\nI feel today')
        self.assertIn('Услышал:', label)
        self.assertIn('I feel today', label)
        self.assertNotIn('Pogovorii', label)

    def test_phonetic_great_not_shown_as_russian(self):
        from ai_app.speech.bilingual import (
            merge_tutor_transcripts,
            phonetic_english_only_line,
            tutor_transcript_label,
        )

        self.assertEqual(phonetic_english_only_line('Гуэйт').lower(), 'great')
        merged = merge_tutor_transcripts(
            'Гуэйт',
            "why don t you ask me about my feelings",
        )
        self.assertEqual(merged.lower(), 'great')
        label = tutor_transcript_label(merged)
        self.assertIn('Услышал:', label)
        self.assertNotIn('по-русски', label)
        self.assertNotIn('Гуэйт', label)

        from ai_app.speech.bilingual import (
            merge_tutor_transcripts,
            tutor_transcript_label,
        )

        ru = 'Можешь поговорить со мной сегодня'
        en = 'can you talk to me today'
        merged = merge_tutor_transcripts(ru, en)
        self.assertNotIn('Можешь', merged)
        self.assertIn('talk', merged.lower())
        label = tutor_transcript_label(merged)
        self.assertIn('Услышал:', label)
        self.assertNotIn('по-русски', label)

    def test_russian_only_skips_am_hallucination(self):
        from ai_app.speech.bilingual import (
            is_meaningful_english_fragment,
            merge_tutor_transcripts,
            tutor_transcript_label,
        )

        ru = 'Поговори со мной сегодня'
        en = 'am am am am am am am am am am am am'
        self.assertFalse(is_meaningful_english_fragment(en))
        merged = merge_tutor_transcripts(ru, en)
        self.assertEqual(merged, ru)
        label = tutor_transcript_label(merged)
        self.assertIn('по-русски', label)
        self.assertNotIn('Услышал: «', label.replace('по-русски', ''))

    def test_stt_contractions_normalized(self):
        from ai_app.speech.bilingual import english_portion_for_tutor, normalize_english_fragment

        self.assertIn("don't", normalize_english_fragment("why don t you ask"))
        self.assertIn("don't", english_portion_for_tutor("why don t you ask me"))

    def test_voice_stt_caps_and_stutter_cleaned(self):
        from ai_app.speech.bilingual import (
            normalize_voice_english_transcript,
            prepare_tutor_voice_transcript,
        )

        raw = 'i would like i would like to talk to you today in english'
        cleaned = normalize_voice_english_transcript(raw)
        self.assertIn('I would like', cleaned, cleaned)
        self.assertIn('English', cleaned)
        self.assertNotIn('i would like i would like', cleaned.lower())
        self.assertEqual(
            prepare_tutor_voice_transcript(raw),
            cleaned,
        )

    def test_adjacent_word_repeat_collapsed(self):
        from ai_app.speech.bilingual import normalize_voice_english_transcript

        self.assertEqual(
            normalize_voice_english_transcript('my my dog is nervous'),
            'My dog is nervous',
        )
        self.assertEqual(
            normalize_voice_english_transcript('I I want to improve'),
            'I want to improve',
        )
        self.assertEqual(
            normalize_voice_english_transcript('talk to to you but im worried'),
            "Talk to you but I'm worried",
        )
        self.assertIn(
            'pronunciation',
            normalize_voice_english_transcript(
                'worried about my english pronouncing',
            ).lower(),
        )

    def test_code_switch_forgotten_russian_words(self):
        from ai_app.speech.bilingual import (
            collapse_voice_fillers,
            is_code_switch_message,
            merge_code_switch_transcript,
            merge_tutor_transcripts,
            tutor_transcript_label,
        )

        en = (
            'I want to Razvehvati ummmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm'
            'ragbiet My english channel'
        )
        ru = 'я хочу развивать и продвигать свой английский канал'
        self.assertNotIn('mmmm', collapse_voice_fillers(en))
        merged = merge_code_switch_transcript(ru, en)
        self.assertTrue(is_code_switch_message(merged))
        self.assertIn('…', merged)
        self.assertIn('развивать', merged)
        self.assertNotIn('Razvehvati', merged)
        self.assertNotIn('ragbiet', merged)

        full = merge_tutor_transcripts(ru, en)
        self.assertIn('забыл слова', full)
        label = tutor_transcript_label(full)
        self.assertIn('Забыл по-английски', label)
        self.assertNotIn('Razvehvati', label)
        self.assertNotIn('mmmm', label)

    def test_forgotten_skips_english_already_in_transcript(self):
        from ai_app.speech.bilingual import (
            merge_code_switch_transcript,
            merge_whisper_tutor_transcript,
        )

        merged = merge_code_switch_transcript(
            'развивать инглишчан',
            'I want to my English channel',
        )
        self.assertIn('развивать', merged.lower())
        self.assertNotIn('инглишчан', merged.lower())

        whisper = merge_whisper_tutor_transcript(
            'I want to развивать my English channel',
        )
        self.assertNotIn('инглишчан', whisper.lower())
        self.assertIn('развивать', whisper.lower())

    def test_launch_misheard_improve_pronunciation(self):
        from ai_app.speech.bilingual import (
            merge_whisper_tutor_transcript,
            scaffold_i_want_to_english_goal,
        )

        raw = (
            'I want to launch it my English pronunciation '
            'what should I do for this'
        )
        scaffolded = scaffold_i_want_to_english_goal(raw)
        self.assertIn('…', scaffolded)
        self.assertIn('улучшать', scaffolded)
        self.assertNotIn('launch', scaffolded.lower())
        self.assertIn('pronunciation', scaffolded.lower())

        merged = merge_whisper_tutor_transcript(raw)
        self.assertIn('улучшать', merged.lower())
        self.assertNotIn('launch', merged.lower())
    def test_would_like_without_mistake_does_not_trigger_polite_rule(self):
        from ai_app.services.rule_hints import suggest_rule_keys

        user = (
            'I would like to practice English and I want you to correct me '
            'if I say something wrong'
        )
        reply = (
            '🇷🇺 <b>По-русски:</b>\n'
            '❌ «if i say in something wrong» → ✅ «if I say something wrong» '
            '(лишнее слово in)\n'
            '[RULE:polite-requests]'
        )
        keys = suggest_rule_keys(user_text=user, tutor_reply=reply, tagged_keys=['polite-requests'])
        self.assertEqual(keys, [])

    def test_capital_i_only_is_not_substantive(self):
        from ai_app.services.rule_hints import (
            is_capitalization_only_mistake,
            reply_has_substantive_grammar_mistakes,
            suggest_rule_keys,
        )

        self.assertTrue(is_capitalization_only_mistake('And i', 'and I'))
        reply = '❌ «And i» → ✅ «and I»'
        self.assertFalse(reply_has_substantive_grammar_mistakes(reply))
        keys = suggest_rule_keys(
            user_text='And i want coffee',
            tutor_reply=reply,
            tagged_keys=['modal-can'],
        )
        self.assertEqual(keys, [])

    def test_want_to_would_like_triggers_polite_rule(self):
        from ai_app.services.rule_hints import suggest_rule_keys

        reply = '❌ «I want coffee» → ✅ «I would like coffee»'
        keys = suggest_rule_keys(user_text='', tutor_reply=reply, tagged_keys=[])
        self.assertEqual(keys, ['polite-requests'])

    def test_read_have_stt_with_ru_forgotten_word(self):
        from ai_app.speech.bilingual import merge_tutor_transcripts, tutor_transcript_label

        ru = 'я хочу развивать свой английский канал'
        en = 'I want to read have my English channel what should I do for it'
        merged = merge_tutor_transcripts(ru, en)
        self.assertIn('забыл слова', merged)
        self.assertIn('развивать', merged)
        self.assertNotIn('read have', merged.lower())
        self.assertIn('What should I do', merged)
        label = tutor_transcript_label(merged)
        self.assertIn('Забыл по-английски', label)
        self.assertIn('What should I do', label)

    def test_spirit_chat_turn_detection(self):
        from ai_app.services.spirit_character import is_spirit_chat_turn

        self.assertTrue(is_spirit_chat_turn(
            "Could you ask me some questions I don't know what to talk about",
        ))
        self.assertTrue(is_spirit_chat_turn('как дела?'))
        self.assertTrue(is_spirit_chat_turn('расскажи о себе'))
        self.assertFalse(is_spirit_chat_turn('what is present simple'))

    def test_grammar_followup_detection_and_target(self):
        from ai_app.services.tutor_context import (
            extract_grammar_followup_target,
            is_grammar_followup_turn,
        )
        from ai_app.services.types import ChatMessage

        history = [
            ChatMessage(
                'user',
                'I want to develop my English channel and get more audience.',
            ),
            ChatMessage(
                'assistant',
                '🇷🇺 <b>По-русски:</b>\n'
                'Услышал: «I want to develop my English channel»\n'
                'Грамматика: Лучше: «I want to grow my English channel and reach more viewers.»',
            ),
        ]
        followup = (
            'Could you please explain better the sentence which I said, '
            'especially grammar of all these sentences?'
        )
        self.assertTrue(is_grammar_followup_turn(followup, history))
        target = extract_grammar_followup_target(
            [*history, ChatMessage('user', followup)],
        )
        self.assertIn('grow my English channel', target)
        self.assertFalse(is_grammar_followup_turn('what is present simple', history))

    def test_i_love_to_travel_plus_russian_books(self):
        from ai_app.speech.bilingual import (
            merge_tutor_transcripts,
            scaffold_i_like_to,
            tutor_transcript_label,
        )

        en = 'I love to travel kniggee'
        sc = scaffold_i_like_to(en)
        self.assertIn('I love to travel', sc)
        self.assertIn('книги', sc)
        self.assertNotIn('kniggee', sc)

        en2 = 'I like to kniggee'
        merged = merge_tutor_transcripts('', en2)
        self.assertIn('книги', merged)
        label = tutor_transcript_label(merged)
        self.assertIn('книги', label)
        self.assertNotIn('kniggee', label)

    def test_i_like_to_mixed_when_ru_pass_empty(self):
        from ai_app.speech.bilingual import (
            is_code_switch_message,
            merge_tutor_transcripts,
            tutor_transcript_label,
        )

        en = 'I like to puta shestertva t citat knigi'
        merged = merge_tutor_transcripts('', en)
        self.assertTrue(is_code_switch_message(merged))
        self.assertIn('I like to', merged)
        self.assertIn('забыл слова', merged)
        self.assertIn('книги', merged)
        label = tutor_transcript_label(merged)
        self.assertIn('Забыл по-английски', label)
        self.assertNotIn('shestertva', label)

    def test_i_like_to_mixed_with_ru_pass(self):
        from ai_app.speech.bilingual import merge_tutor_transcripts, tutor_transcript_label

        ru = 'я люблю путешествовать и читать книги'
        en = 'I like to puta shestertva t citat knigi'
        merged = merge_tutor_transcripts(ru, en)
        self.assertIn('I like to', merged)
        self.assertIn('забыл слова', merged)
        self.assertIn('книги', merged)
        self.assertIn('читать', merged)

    def test_pure_russian_ignores_en_translation_hallucination(self):
        from ai_app.speech.bilingual import (
            is_pure_russian_speech,
            merge_tutor_transcripts,
            tutor_transcript_label,
        )

        ru = (
            'Объясни пожалуйста лучше предложение которое я сказал '
            'особенно грамматику всех этих предложений'
        )
        en = (
            'Could you please explain better the sentence which I said, '
            'especially grammar of all these sentences?'
        )
        self.assertTrue(is_pure_russian_speech(ru, en))
        merged = merge_tutor_transcripts(ru, en)
        self.assertIn('Объясни', merged)
        self.assertNotIn('Could you please', merged)
        label = tutor_transcript_label(merged)
        self.assertIn('по-русски', label)

    def test_identical_en_passes_deduped(self):
        from ai_app.speech.bilingual import merge_tutor_transcripts, tutor_transcript_label

        text = (
            'Could you please explain better the sentence which I said, '
            'especially grammar of all these sentences?'
        )
        merged = merge_tutor_transcripts(text, text)
        self.assertEqual(merged.count('Could you please'), 1)
        label = tutor_transcript_label(merged)
        self.assertNotIn('RU:', label)
        self.assertNotIn('EN:', label)

    def test_mixed_embedded_russian_word_in_en_pass(self):
        from ai_app.speech.bilingual import merge_tutor_transcripts, tutor_transcript_label

        ru = (
            'Я хочу развивать мой английский канал, как я планирую на то, '
            'что я постараюсь на 5 дней, и так далее я хочу получить больше зрителей.'
        )
        en = (
            'I want to развивать my English channel, like I planned to post at least '
            'five posts a day, and this way I want to get more audience.'
        )
        merged = merge_tutor_transcripts(ru, en)
        self.assertIn('I want to', merged)
        self.assertIn('развивать', merged)
        self.assertNotIn('Я хочу развивать', merged.split('\n')[0])
        label = tutor_transcript_label(merged)
        self.assertIn('Забыл по-английски', label)

    def test_pure_russian_ignores_polish_en_pass(self):
        from ai_app.speech.bilingual import (
            is_pure_russian_speech,
            merge_tutor_transcripts,
            tutor_transcript_label,
        )

        ru = 'Ты понимаешь русскую речь'
        en = 'Czy poniesiesz ralph ruskowicz'
        self.assertTrue(is_pure_russian_speech(ru, en))
        merged = merge_tutor_transcripts(ru, en)
        self.assertEqual(merged, ru)
        label = tutor_transcript_label(merged)
        self.assertIn('по-русски', label)
        self.assertNotIn('Услышал: «', label.replace('по-русски', ''))

    def test_pure_russian_ignores_latin_en_pass(self):
        from ai_app.speech.bilingual import (
            is_pure_russian_speech,
            merge_tutor_transcripts,
            tutor_transcript_label,
        )

        ru = 'Какие темы ты можешь со мной поговорить'
        en = 'Jakie temy tu modus zamyszysz I pogovorid'
        self.assertTrue(is_pure_russian_speech(ru, en))
        merged = merge_tutor_transcripts(ru, en)
        self.assertEqual(merged, ru)
        self.assertNotIn('Jakie', merged)
        self.assertNotIn('забыл слова', merged.lower())
        label = tutor_transcript_label(merged)
        self.assertIn('по-русски', label)
        self.assertNotIn('Забыл по-английски', label)

    def test_english_speech_drops_phantom_ru_pass(self):
        from ai_app.speech.bilingual import merge_tutor_transcripts, tutor_transcript_label

        ru = 'Я очень люблю путешествовать и я собака.'
        en = 'I would like to travel a lot and I have собака.'
        merged = merge_tutor_transcripts(ru, en)
        self.assertIn('I would like to travel', merged)
        self.assertIn('собака', merged)
        self.assertNotIn('Я очень люблю', merged)
        self.assertNotIn('\nЯ', merged.split('\n')[0] if '\n' in merged else merged)
        label = tutor_transcript_label(merged)
        self.assertIn('Услышал:', label)
        self.assertNotIn('RU:', label)
        self.assertNotIn('EN:', label)
        self.assertIn('собака', label)

    def test_pure_english_drops_phantom_ru_pass(self):
        from ai_app.speech.bilingual import merge_tutor_transcripts, tutor_transcript_label

        ru = 'Кудибил самдаев'
        en = 'Could you build some dialect with me to practice English'
        merged = merge_tutor_transcripts(ru, en)
        self.assertNotIn('\n', merged)
        self.assertIn('Could you build', merged)
        self.assertNotIn('Кудибил', merged)
        label = tutor_transcript_label(merged)
        self.assertIn('Услышал:', label)
        self.assertNotIn('по-русски', label)

    def test_en_then_ru_questions_about_place(self):
        from ai_app.speech.bilingual import (
            merge_tutor_transcripts,
            merge_whisper_tutor_transcript,
            scaffold_i_have_questions_about,
        )

        ru = 'место где я действительно хочу быть'
        en = 'I have some questions about'
        merged = merge_tutor_transcripts(ru, en)
        self.assertIn('забыл слова', merged)
        self.assertIn('I have some questions about', merged)
        self.assertIn('…', merged)
        self.assertIn('место', merged)
        self.assertIn('действительно', merged)
        self.assertNotIn('Mesters', merged)

        garbage = (
            'I have some questions about Mesters that you mena est somnenia etat'
        )
        repaired = merge_whisper_tutor_transcript(garbage)
        self.assertIn('I have some questions about', repaired)
        self.assertNotIn('Mesters', repaired)
        self.assertIn('…', repaired)

        scaffold = scaffold_i_have_questions_about(
            'I have some questions about Mesters that you'
        )
        self.assertIn('…', scaffold)
        self.assertNotIn('Mesters', scaffold)

    def test_stt_vocabulary_fix_does_not_trigger_wh_rule(self):
        from ai_app.services.rule_hints import suggest_rule_keys

        reply = (
            '❌ «read have» → ✅ «develop»\n'
            '[RULE:wh-questions-basics]'
        )
        keys = suggest_rule_keys(
            user_text='',
            tutor_reply=reply,
            tagged_keys=['wh-questions-basics'],
        )
        self.assertEqual(keys, [])

    def test_thompson_a_woman_sanitized(self):
        from ai_app.speech.bilingual import (
            looks_like_stt_word_salad,
            prepare_tutor_voice_transcript,
            sanitize_stt_garbage_clauses,
        )

        raw = (
            'I would like to talk to you in English could you correct me '
            'if I said thompson a woman'
        )
        self.assertTrue(looks_like_stt_word_salad('thompson a woman'))
        cleaned = sanitize_stt_garbage_clauses(raw)
        self.assertIn('if I said …', cleaned)
        self.assertNotIn('thompson', cleaned.lower())
        self.assertIn('…', prepare_tutor_voice_transcript(raw))


class WhisperSTTTests(TestCase):
    def test_split_whisper_mixed(self):
        from ai_app.speech.bilingual import merge_whisper_tutor_transcript, split_whisper_mixed

        ru, en = split_whisper_mixed('я хочу развивать my English channel')
        self.assertIn('развивать', ru)
        self.assertIn('English channel', en)
        merged = merge_whisper_tutor_transcript(
            'I want to развивать my English channel what should I do for it'
        )
        self.assertTrue(merged)
        self.assertNotIn('read have', merged.lower())

    def test_whisper_transcribe_via_proxy(self):
        from unittest.mock import AsyncMock, patch

        from ai_app.speech.whisper import OpenAIWhisperSTT

        async def _run():
            stt = OpenAIWhisperSTT(
                api_key='test-key',
                base_url='https://proxy.example/v1',
                model='whisper-large-v3-turbo',
            )
            fake_response = type('R', (), {
                'status_code': 200,
                'content': b'{"text":"Hello world"}',
                'json': lambda self: {'text': 'Hello world'},
                'text': '',
            })()
            with patch('ai_app.speech.whisper.httpx.AsyncClient') as client_cls:
                client = AsyncMock()
                client_cls.return_value.__aenter__.return_value = client
                client.post.return_value = fake_response
                tr = await stt.transcribe(b'fake', lang='auto')
                self.assertEqual(tr.text, 'Hello world')
                self.assertEqual(tr.provider, 'whisper')
                call_kwargs = client.post.call_args.kwargs
                self.assertIn('/audio/transcriptions', call_kwargs['url'] if 'url' in call_kwargs else client.post.call_args[0][0])

        import asyncio
        asyncio.run(_run())

    def test_whisper_model_candidates_include_default_after_tier_primary(self):
        from django.test import override_settings

        from ai_app.speech.whisper import _whisper_model_candidates

        with override_settings(
            OPENAI_WHISPER_MODEL='whisper-large-v3-turbo',
            OPENAI_WHISPER_FALLBACK_MODELS='whisper-large-v3,whisper-1',
        ):
            models = _whisper_model_candidates('gpt-4o-mini-transcribe')
        self.assertEqual(
            models,
            ['gpt-4o-mini-transcribe', 'whisper-large-v3-turbo', 'whisper-large-v3', 'whisper-1'],
        )

    def test_whisper_falls_back_when_tier_model_forbidden(self):
        from unittest.mock import AsyncMock, patch

        from ai_app.speech.whisper import OpenAIWhisperSTT

        async def _run():
            stt = OpenAIWhisperSTT(
                api_key='test-key',
                base_url='https://proxy.example/v1',
                model='gpt-4o-mini-transcribe',
            )

            def _response_for_model(*_args, **kwargs):
                model = kwargs.get('data', {}).get('model', '')
                if model == 'gpt-4o-mini-transcribe':
                    return type('R', (), {
                        'status_code': 403,
                        'content': b'forbidden',
                        'json': lambda self: {},
                        'text': 'forbidden',
                    })()
                return type('R', (), {
                    'status_code': 200,
                    'content': b'{"text":"privet"}',
                    'json': lambda self: {'text': 'privet'},
                    'text': '',
                })()

            with patch('ai_app.speech.whisper.httpx.AsyncClient') as client_cls:
                client = AsyncMock()
                client_cls.return_value.__aenter__.return_value = client
                client.post.side_effect = _response_for_model
                with patch('ai_app.speech.whisper._whisper_model_candidates') as candidates:
                    candidates.return_value = [
                        'gpt-4o-mini-transcribe',
                        'whisper-large-v3-turbo',
                    ]
                    tr = await stt.transcribe(b'fake', lang='ru-RU')
                self.assertEqual(tr.text, 'privet')
                self.assertTrue(tr.ok)

        import asyncio
        asyncio.run(_run())

    def test_get_tutor_stt_prefers_whisper_with_openai_key(self):
        from django.test import override_settings

        from ai_app.speech.registry import get_tutor_stt_provider

        with override_settings(OPENAI_API_KEY='sk-test', STT_TUTOR_PROVIDER='auto'):
            provider = get_tutor_stt_provider()
            self.assertEqual(provider.name, 'whisper')
