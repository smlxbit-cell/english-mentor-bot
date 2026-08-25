"""Word training drill: EN→RU, RU→EN, listen→RU, context gap (new); recall for SRS review."""

from __future__ import annotations

import random
import re
from typing import Any

STEPS_NEW = ('meaning', 'english', 'listening', 'context')
STEPS_REVIEW = ('recall',)
TEXT_STEPS = ('meaning', 'english')
DRILL_PHASE_TEXT = 'text'
DRILL_PHASE_LISTENING = 'listening'
DRILL_PHASE_CONTEXT = 'context'
_GAP = '______'

STEP_LABELS = {
    'meaning': '🇬🇧→🇷🇺',
    'english': '🇷🇺→🇬🇧',
    'listening': '👂→🇷🇺',
    'context': '📝→🇬🇧',
    'recall': '🇷🇺→🇬🇧',
}


def steps_for(*, new_words: bool) -> tuple[str, ...]:
    return STEPS_NEW if new_words else STEPS_REVIEW


def initial_drill_step(*, new_words: bool) -> str:
    return TEXT_STEPS[0] if new_words else STEPS_REVIEW[0]


def advance_drill(
    *,
    words: list[dict[str, Any]],
    new_words: bool,
    phase: str,
    word_index: int,
    step: str,
    listening_index: int,
    listening_order: list[int] | None,
    context_index: int = 0,
    context_order: list[int] | None = None,
) -> dict[str, Any] | None:
    """
    Return the next drill cursor, or None when the session is complete.

    New-word flow: text round → shuffled listening → shuffled context gap.
    """
    if not words:
        return None

    if not new_words:
        if word_index + 1 >= len(words):
            return None
        return {
            'phase': phase,
            'word_index': word_index + 1,
            'step': STEPS_REVIEW[0],
            'listening_index': listening_index,
            'listening_order': listening_order,
            'context_index': context_index,
            'context_order': context_order,
        }

    if phase == DRILL_PHASE_TEXT:
        if step == 'meaning':
            return {
                'phase': phase,
                'word_index': word_index,
                'step': 'english',
                'listening_index': listening_index,
                'listening_order': listening_order,
                'context_index': context_index,
                'context_order': context_order,
            }
        if word_index + 1 < len(words):
            return {
                'phase': phase,
                'word_index': word_index + 1,
                'step': 'meaning',
                'listening_index': listening_index,
                'listening_order': listening_order,
                'context_index': context_index,
                'context_order': context_order,
            }
        order = list(range(len(words)))
        random.shuffle(order)
        return {
            'phase': DRILL_PHASE_LISTENING,
            'word_index': order[0],
            'step': 'listening',
            'listening_index': 0,
            'listening_order': order,
            'context_index': context_index,
            'context_order': context_order,
        }

    if phase == DRILL_PHASE_LISTENING:
        order = listening_order or list(range(len(words)))
        next_listening = listening_index + 1
        if next_listening < len(order):
            return {
                'phase': DRILL_PHASE_LISTENING,
                'word_index': order[next_listening],
                'step': 'listening',
                'listening_index': next_listening,
                'listening_order': order,
                'context_index': context_index,
                'context_order': context_order,
            }
        ctx_order = context_eligible_indices(words)
        if not ctx_order:
            return None
        random.shuffle(ctx_order)
        return {
            'phase': DRILL_PHASE_CONTEXT,
            'word_index': ctx_order[0],
            'step': 'context',
            'listening_index': listening_index,
            'listening_order': order,
            'context_index': 0,
            'context_order': ctx_order,
        }

    ctx_order = context_order or list(range(len(words)))
    next_context = context_index + 1
    if next_context >= len(ctx_order):
        return None
    return {
        'phase': DRILL_PHASE_CONTEXT,
        'word_index': ctx_order[next_context],
        'step': 'context',
        'listening_index': listening_index,
        'listening_order': listening_order,
        'context_index': next_context,
        'context_order': ctx_order,
    }


def drill_progress_pos(
    *,
    phase: str,
    word_index: int,
    listening_index: int,
    context_index: int = 0,
) -> int:
    """1-based position shown in drill headers."""
    if phase == DRILL_PHASE_LISTENING:
        return listening_index + 1
    if phase == DRILL_PHASE_CONTEXT:
        return context_index + 1
    return word_index + 1


def context_eligible_indices(words: list[dict[str, Any]]) -> list[int]:
    from .example_enrich import is_valid_context_example

    return [i for i, word in enumerate(words) if is_valid_context_example(word)]


def step_label(step: str) -> str:
    return STEP_LABELS.get(step, step)


def blank_headword(sentence: str, headword: str) -> str | None:
    if not sentence or not headword:
        return None
    pattern = re.compile(r'\b' + re.escape(headword) + r'\b', re.I)
    if pattern.search(sentence):
        return pattern.sub(_GAP, sentence, count=1)
    low = sentence.lower()
    hw = headword.lower()
    idx = low.find(hw)
    if idx >= 0:
        return sentence[:idx] + _GAP + sentence[idx + len(headword):]
    return None


def pick_distractors(
    target: dict[str, Any],
    pool: list[dict[str, Any]],
    *,
    count: int = 3,
) -> list[dict[str, Any]]:
    target_en = (target.get('english') or '').lower()
    candidates = [
        w for w in pool
        if (w.get('english') or '').lower() != target_en
        and (w.get('english') or '').strip()
    ]
    random.shuffle(candidates)
    return candidates[:count]


def build_english_choice(
    word: dict[str, Any],
    pool: list[dict[str, Any]],
    *,
    option_count: int = 4,
) -> tuple[list[dict[str, Any]], int]:
    distractors = pick_distractors(word, pool, count=option_count - 1)
    options = distractors + [word]
    random.shuffle(options)
    correct_idx = next(
        i for i, w in enumerate(options)
        if (w.get('english') or '').lower() == (word.get('english') or '').lower()
    )
    return options, correct_idx


def build_translation_choice(
    word: dict[str, Any],
    pool: list[dict[str, Any]],
    *,
    option_count: int = 4,
) -> tuple[list[str], int]:
    target_tr = (word.get('translation') or '').strip()
    translations: list[str] = []
    for w in pool:
        tr = (w.get('translation') or '').strip()
        if tr and tr != target_tr and tr not in translations:
            translations.append(tr)
    random.shuffle(translations)
    options = translations[: option_count - 1] + [target_tr]
    random.shuffle(options)
    correct_idx = options.index(target_tr)
    return options, correct_idx


def option_button_label(text: str, *, max_len: int = 36) -> str:
    t = (text or '').strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + '…'


def append_example_lines(text: str, word: dict[str, Any]) -> str:
    """Append EN example + RU gloss when present."""
    example = (word.get('example') or '').strip()
    if not example:
        return text
    example_ru = (word.get('example_ru') or '').strip()
    msg = f'{text}\n📝 {example}'
    if example_ru:
        msg += f'\n   ({example_ru})'
    return msg


def format_intro_card(
    *,
    pos: int,
    total: int,
    level: str,
    english: str,
    translation: str,
    learn_count: int,
    known_count: int,
    example: str = '',
    example_ru: str = '',
) -> str:
    text = (
        f'📘 <b>{pos}/{total}</b> · {level.upper()}\n\n'
        f'🇬🇧 <b>{english}</b>\n'
        f'🇷🇺 {translation}\n\n'
        f'<i>учить {learn_count} · уже знаю {known_count}</i>'
    )
    if example:
        text += f'\n📝 {example}'
        if example_ru:
            text += f'\n   ({example_ru})'
    return text


def format_intro_summary(*, learn_count: int, known_count: int) -> str:
    return f'✅ Знаю {known_count} · учить {learn_count} → тест'


def format_drill_header(*, word_pos: int, word_total: int, step: str) -> str:
    return f'🎯 {word_pos}/{word_total} · {step_label(step)}'


def drill_tts_text(word: dict[str, Any]) -> str:
    """English phrase to voice for the current drill word."""
    en = (word.get('english') or '').strip()
    ex = (word.get('example') or '').strip()
    return en if not ex else f'{en}. {ex}'


def drill_listen_tts_text(word: dict[str, Any]) -> str:
    """Headword only — listening step tests recognition by ear."""
    return (word.get('english') or '').strip()


def prepare_context_drill(word: dict[str, Any]) -> dict[str, str] | None:
    """Build gap sentence, RU gloss, and TTS text for the context step."""
    from .example_enrich import is_valid_context_example

    if not is_valid_context_example(word):
        return None
    example = (word.get('example') or '').strip()
    example_ru = (word.get('example_ru') or '').strip()
    headword = (word.get('english') or '').strip()
    gap = blank_headword(example, headword)
    if not gap:
        return None
    return {
        'example': example,
        'example_ru': example_ru,
        'gap_sentence': gap,
        'tts': example,
    }


def format_drill_context_prompt(
    header: str,
    *,
    gap_sentence: str,
    example_ru: str,
) -> str:
    lines = [header, '']
    if example_ru:
        lines.append(f'🇷🇺 «{example_ru}»')
        lines.append('')
    lines.append(f'🇬🇧 {gap_sentence}')
    lines.append('')
    lines.append('Какое слово пропущено?')
    return '\n'.join(lines)


def format_context_correct(*, word: dict[str, Any], example: str, example_ru: str) -> str:
    msg = f'✅ <b>{word["english"]}</b> — {word["translation"]}'
    if example:
        msg += f'\n🇬🇧 {example}'
    if example_ru:
        msg += f'\n🇷🇺 {example_ru}'
    return msg


def format_context_wrong(
    *,
    picked: dict[str, Any],
    correct: dict[str, Any],
    options: list[dict[str, Any]],
    example: str,
    example_ru: str,
) -> str:
    picked_en = picked.get('english') or '?'
    picked_ru = (picked.get('translation') or '').strip()
    correct_ru = (correct.get('translation') or '').strip()
    msg = f'❌ <b>{picked_en}</b>'
    if picked_ru:
        msg += f' — «{picked_ru}»'
    msg += f'\nНужно слово для примера.\n\n'
    if example_ru:
        msg += f'🇷🇺 «{example_ru}»\n'
    if example:
        msg += f'🇬🇧 {example}\n\n'
    msg += f'✅ <b>{correct["english"]}</b> — {correct_ru}\n\n'
    msg += '<b>Варианты:</b>\n'
    for opt in options:
        tr = (opt.get('translation') or '').strip()
        mark = ' ✓' if (
            (opt.get('english') or '').lower() == (correct.get('english') or '').lower()
        ) else ''
        msg += f'• <b>{opt["english"]}</b> — {tr}{mark}\n'
    return msg.rstrip()


def format_option_translations_hint(options: list[dict[str, Any]]) -> str:
    lines = ['🇷🇺 <b>Переводы вариантов</b>', '']
    for opt in options:
        tr = (opt.get('translation') or '').strip()
        lines.append(f'🇬🇧 <b>{opt["english"]}</b> — {tr}')
    return '\n'.join(lines)


def format_drill_meaning_prompt(header: str, english: str) -> str:
    return f'{header}\n\n🇬🇧 <b>{english}</b>\n\nКакой перевод?'


def format_drill_english_prompt(header: str, translation: str) -> str:
    return f'{header}\n\n🇷🇺 <b>{translation}</b>\n\nКак по-английски?'


def format_drill_listening_prompt(header: str) -> str:
    return f'{header}\n\n👂 <b>Слушай</b> · какой перевод?'


def format_drill_listening_hint(english: str) -> str:
    return f'👀 <b>{english}</b>'


def format_drill_recall_prompt(header: str, translation: str) -> str:
    return (
        f'{header}\n\n'
        f'🇷🇺 «{translation}»\n'
        '✍️ Напишите · 🎙️ Скажите'
    )


def format_word_cheatsheet(words: list[dict[str, Any]]) -> str:
    lines = ['📖 <b>Все слова</b>', '']
    for w in words:
        block = f'🇬🇧 <b>{w["english"]}</b> — {w["translation"]}'
        lines.append(append_example_lines(block, w))
    return '\n'.join(lines)


def format_choice_correct(word: dict[str, Any]) -> str:
    msg = f'✅ <b>{word["english"]}</b> — {word["translation"]}'
    return append_example_lines(msg, word)


def format_meaning_wrong(
    *,
    picked: str,
    correct: dict[str, Any],
    pool: list[dict[str, Any]],
) -> str:
    """EN→RU: user picked wrong Russian option."""
    picked_word = next(
        (w for w in pool if (w.get('translation') or '').strip() == picked.strip()),
        None,
    )
    if picked_word:
        wrong = (
            f'❌ «{picked}» — это <b>{picked_word["english"]}</b>, '
            f'а вопрос про <b>{correct["english"]}</b>.'
        )
    else:
        wrong = f'❌ «{picked}» — не подходит к <b>{correct["english"]}</b>.'
    msg = f'{wrong}\n\n✅ <b>{correct["english"]}</b> — {correct["translation"]}'
    return append_example_lines(msg, correct)


def format_english_wrong(*, picked: dict[str, Any], correct: dict[str, Any]) -> str:
    """RU→EN: user picked wrong English option."""
    picked_en = picked.get('english') or '?'
    picked_ru = (picked.get('translation') or '').strip()
    correct_ru = (correct.get('translation') or '').strip()
    msg = f'❌ <b>{picked_en}</b>'
    if picked_ru:
        msg += f' — «{picked_ru}»'
    msg += f'\nЭто не ответ на «{correct_ru}».\n\n'
    msg += f'✅ <b>{correct["english"]}</b> — {correct_ru}'
    return append_example_lines(msg, correct)


def format_choice_wrong(*, picked: dict[str, Any], correct: dict[str, Any]) -> str:
    return format_english_wrong(picked=picked, correct=correct)


def format_translation_choice_wrong(
    *,
    picked: str,
    correct: dict[str, Any],
    pool: list[dict[str, Any]],
) -> str:
    return format_meaning_wrong(picked=picked, correct=correct, pool=pool)


def format_recall_correct(word: dict[str, Any], *, heard: str = '') -> str:
    msg = format_choice_correct(word)
    if heard and heard.strip():
        msg += f'\n(услышал: «{heard.strip()}»)'
    return msg


def format_recall_wrong(word: dict[str, Any], *, heard: str = '') -> str:
    heard = (heard or '').strip()
    msg = f'❌ Не «{heard}»' if heard else '❌ Неверно'
    msg += (
        f'\n\n✅ <b>{word["english"]}</b> — {word["translation"]}'
    )
    return append_example_lines(msg, word)
