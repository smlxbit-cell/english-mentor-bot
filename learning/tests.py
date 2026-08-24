import json
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from learning.management.commands.seed_word_bank import collect_word_bank_rows
from learning.models import WordBankEntry
from learning.word_bank.loader import load_json_file, parse_row
from learning.word_bank.normalize import word_slug
from learning.word_bank.seed_words import iter_builtin_rows


class WordSlugTests(TestCase):
    def test_slug_basic(self):
        self.assertEqual(word_slug('Thank you'), 'thank-you')

    def test_slug_strips_punctuation(self):
        self.assertEqual(word_slug("don't"), 'dont')


class ParseRowTests(TestCase):
    def test_minimal_row(self):
        row = parse_row({'english': 'hello', 'translation': 'привет', 'cefr_level': 'a1'})
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row['slug'], 'hello')
        self.assertEqual(row['cefr_level'], 'a1')

    def test_skips_incomplete(self):
        self.assertIsNone(parse_row({'english': 'hello'}))


class LoaderTests(TestCase):
    def test_load_json_array(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sample.json'
            path.write_text(
                json.dumps([{'english': 'tea', 'translation': 'чай', 'level': 'a1'}]),
                encoding='utf-8',
            )
            rows = load_json_file(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['english'], 'tea')


class SeedCorpusTests(TestCase):
    def test_builtin_has_all_levels(self):
        rows = iter_builtin_rows()
        levels = {r['cefr_level'] for r in rows}
        self.assertEqual(levels, {'a1', 'a2', 'b1', 'b2', 'c1'})
        self.assertGreaterEqual(len(rows), 250)

    def test_collect_includes_builtin(self):
        merged = collect_word_bank_rows()
        self.assertIn('hello', merged)
        self.assertIn('coffee', merged)

    def test_collect_with_remote_cache(self):
        data_dir = Path(settings.BASE_DIR) / 'learning' / 'data' / 'word_bank'
        if not (data_dir / 'remote.json').is_file():
            self.skipTest('remote.json not cached')
        merged = collect_word_bank_rows(data_dir=data_dir, include_remote=True)
        self.assertGreater(len(merged), 500)


class WordBankServiceTests(TestCase):
    def setUp(self):
        from users_app.models import UserProfile
        call_command('seed_word_bank', include_remote=True)
        self.profile = UserProfile.objects.create(telegram_id=999001, first_name='Test')

    def test_mark_known_updates_stats(self):
        from learning.word_bank.service import get_level_stats, mark_bank_entry
        from learning.models import WordBankEntry
        from progress_app.models import UserWordBankStatus

        entry = WordBankEntry.objects.filter(cefr_level='a1').first()
        self.assertIsNotNone(entry)
        mark_bank_entry(self.profile.id, entry.id, UserWordBankStatus.Status.KNOWN)
        stat = get_level_stats(self.profile.id, 'a1')
        self.assertGreaterEqual(stat['known'], 1)


class TopicNavigationTests(TestCase):
    def test_canonical_aliases(self):
        from learning.word_bank.navigation import canonical_topic, normalize_topics, topic_label

        self.assertEqual(canonical_topic('food and drink'), 'food')
        self.assertEqual(canonical_topic('work and career'), 'work')
        self.assertEqual(normalize_topics(['remote']), ['general'])
        self.assertEqual(normalize_topics(['travel', 'food and drink']), ['travel', 'food'])
        self.assertIn('Еда', topic_label('food'))

    def test_parse_paged_callback(self):
        from learning.word_bank.navigation import parse_paged_callback

        self.assertEqual(parse_paged_callback('words:bank:topic:food:2', 'words:bank:topic:'), ('food', 2))
        self.assertEqual(parse_paged_callback('words:dict:level:a1:0', 'words:dict:level:'), ('a1', 0))
        self.assertIsNone(parse_paged_callback('words:bank:topic:food', 'words:bank:topic:'))


class TopicClassifierTests(TestCase):
    def test_classify_known_words(self):
        from learning.word_bank.topic_classifier import classify_word, resolve_topics

        self.assertIn('food', classify_word('coffee', 'кофе'))
        self.assertIn('travel', classify_word('airport', 'аэропорт'))
        self.assertEqual(resolve_topics(['food and drink'], english='tea', translation='чай'), ['food'])

    def test_remote_resolves_to_topic_not_general_only(self):
        from learning.word_bank.topic_classifier import resolve_topics

        topics = resolve_topics(['remote'], english='coffee', translation='кофе')
        self.assertNotEqual(topics, ['general'])


class SeedWordBankCommandTests(TestCase):
    def test_seed_creates_entries(self):
        from django.core.management import call_command

        call_command('seed_word_bank', include_remote=True)
        self.assertGreater(WordBankEntry.objects.count(), 500)
        hello = WordBankEntry.objects.get(slug='hello')
        self.assertEqual(hello.translation, 'привет')
        self.assertEqual(hello.cefr_level, 'a1')

    def test_seed_is_idempotent(self):
        from django.core.management import call_command

        call_command('seed_word_bank', include_remote=True)
        count_first = WordBankEntry.objects.count()
        call_command('seed_word_bank', include_remote=True)
        self.assertEqual(WordBankEntry.objects.count(), count_first)


class WordDrillTests(SimpleTestCase):
    def test_build_english_choice_includes_target(self):
        from learning.word_bank.drill import build_english_choice, steps_for

        self.assertEqual(steps_for(new_words=True), ('meaning', 'english', 'listening', 'context'))
        self.assertEqual(steps_for(new_words=False), ('recall',))
        target = {'english': 'coffee', 'translation': 'кофе'}
        pool = [
            target,
            {'english': 'tea', 'translation': 'чай'},
            {'english': 'water', 'translation': 'вода'},
            {'english': 'milk', 'translation': 'молоко'},
        ]
        options, idx = build_english_choice(target, pool)
        self.assertEqual(len(options), 4)
        self.assertEqual(options[idx]['english'], 'coffee')

    def test_advance_drill_text_before_listening(self):
        from learning.word_bank.drill import (
            DRILL_PHASE_CONTEXT,
            DRILL_PHASE_LISTENING,
            DRILL_PHASE_TEXT,
            advance_drill,
        )

        words = [
            {'english': 'chip', 'translation': 'чип', 'example': 'A small chip.'},
            {'english': 'board', 'translation': 'доска', 'example': 'A wooden board.'},
        ]
        state = advance_drill(
            words=words,
            new_words=True,
            phase=DRILL_PHASE_TEXT,
            word_index=0,
            step='meaning',
            listening_index=0,
            listening_order=None,
        )
        self.assertEqual(state['step'], 'english')
        self.assertEqual(state['word_index'], 0)

        state = advance_drill(
            words=words,
            new_words=True,
            phase=DRILL_PHASE_TEXT,
            word_index=0,
            step='english',
            listening_index=0,
            listening_order=None,
        )
        self.assertEqual(state['step'], 'meaning')
        self.assertEqual(state['word_index'], 1)

        state = advance_drill(
            words=words,
            new_words=True,
            phase=DRILL_PHASE_TEXT,
            word_index=1,
            step='english',
            listening_index=0,
            listening_order=None,
        )
        self.assertEqual(state['phase'], DRILL_PHASE_LISTENING)
        self.assertEqual(state['step'], 'listening')
        self.assertEqual(len(state['listening_order']), 2)

        last = state
        while last and last['phase'] == DRILL_PHASE_LISTENING:
            nxt = advance_drill(
                words=words,
                new_words=True,
                phase=last['phase'],
                word_index=last['word_index'],
                step=last['step'],
                listening_index=last['listening_index'],
                listening_order=last['listening_order'],
                context_index=last.get('context_index', 0),
                context_order=last.get('context_order'),
            )
            if nxt and nxt['phase'] == DRILL_PHASE_CONTEXT and last['phase'] == DRILL_PHASE_LISTENING:
                last = nxt
                break
            last = nxt
            self.assertIsNotNone(last)

        self.assertEqual(last['phase'], DRILL_PHASE_CONTEXT)
        self.assertEqual(last['step'], 'context')

        while last and last['phase'] == DRILL_PHASE_CONTEXT:
            nxt = advance_drill(
                words=words,
                new_words=True,
                phase=last['phase'],
                word_index=last['word_index'],
                step=last['step'],
                listening_index=last['listening_index'],
                listening_order=last['listening_order'],
                context_index=last['context_index'],
                context_order=last['context_order'],
            )
            if nxt is None:
                break
            last = nxt

        done = advance_drill(
            words=words,
            new_words=True,
            phase=last['phase'],
            word_index=last['word_index'],
            step=last['step'],
            listening_index=last['listening_index'],
            listening_order=last['listening_order'],
            context_index=last['context_index'],
            context_order=last['context_order'],
        )
        self.assertIsNone(done)

    def test_prepare_context_drill_blanks_headword(self):
        from learning.word_bank.drill import prepare_context_drill

        word = {
            'english': 'coffee',
            'translation': 'кофе',
            'example': 'I drink coffee every day.',
            'example_ru': 'Я пью кофе каждый день.',
        }
        ctx = prepare_context_drill(word)
        self.assertIn('______', ctx['gap_sentence'])
        self.assertNotIn('coffee', ctx['gap_sentence'].lower())
        self.assertIn('coffee', ctx['tts'].lower())
        self.assertEqual(ctx['example_ru'], 'Я пью кофе каждый день.')

    def test_words_count_ru(self):
        from learning.word_bank.service import words_count_ru

        self.assertEqual(words_count_ru(1), '1 слово')
        self.assertEqual(words_count_ru(3), '3 слова')
        self.assertEqual(words_count_ru(43), '43 слова')

    def test_wrong_feedback_explains_mismatch(self):
        from learning.word_bank.drill import format_english_wrong, format_meaning_wrong

        pool = [
            {'english': 'admire', 'translation': 'восхищаться'},
            {'english': 'ache', 'translation': 'боль'},
        ]
        msg = format_meaning_wrong(
            picked='боль',
            correct=pool[0],
            pool=pool,
        )
        self.assertIn('ache', msg)
        self.assertIn('admire', msg)
        msg2 = format_english_wrong(
            picked=pool[1],
            correct=pool[0],
        )
        self.assertIn('восхищаться', msg2)
        self.assertIn('admire', msg2)
