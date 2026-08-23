"""Word training drill: EN→RU choice, RU→EN choice (new); recall for SRS review."""

from __future__ import annotations

import random
from typing import Any

STEPS_NEW = ('meaning', 'english')
STEPS_REVIEW = ('recall',)

STEP_LABELS = {
    'meaning': '🇬🇧→🇷🇺',
    'english': '🇷🇺→🇬🇧',
    'recall': '🇷🇺→🇬🇧',
}


def steps_for(*, new_words: bool) -> tuple[str, ...]:
    return STEPS_NEW if new_words else STEPS_REVIEW


def step_label(step: str) -> str:
    return STEP_LABELS.get(step, step)


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


def format_intro_card(
    *,
    pos: int,
    total: int,
    level: str,
    english: str,
    translation: str,
    learn_count: int,
    known_count: int,
) -> str:
    return (
        f'📘 <b>{pos}/{total}</b> · {level.upper()}\n\n'
        f'🇬🇧 <b>{english}</b>\n'
        f'🇷🇺 {translation}\n\n'
        f'<i>учить {learn_count} · знаю {known_count}</i>'
    )


def format_intro_summary(*, learn_count: int, known_count: int) -> str:
    return f'✅ Знаю {known_count} · учить {learn_count} → тест'


def format_drill_header(*, word_pos: int, word_total: int, step: str) -> str:
    return f'🎯 {word_pos}/{word_total} · {step_label(step)}'


def format_drill_meaning_prompt(header: str, english: str) -> str:
    return f'{header}\n\n🇬🇧 <b>{english}</b>\n\nКакой перевод?'


def format_drill_english_prompt(header: str, translation: str) -> str:
    return f'{header}\n\n🇷🇺 <b>{translation}</b>\n\nКак по-английски?'


def format_drill_recall_prompt(header: str, translation: str) -> str:
    return (
        f'{header}\n\n'
        f'🇷🇺 «{translation}»\n'
        '✍️ Напишите · 🎙️ Скажите'
    )


def format_word_cheatsheet(words: list[dict[str, Any]]) -> str:
    lines = ['📖 <b>Все слова</b>', '']
    for w in words:
        lines.append(f'🇬🇧 <b>{w["english"]}</b> — {w["translation"]}')
        if w.get('example'):
            lines.append(f'   📝 {w["example"]}')
    return '\n'.join(lines)


def format_choice_correct(word: dict[str, Any]) -> str:
    msg = f'✅ <b>{word["english"]}</b> — {word["translation"]}'
    if word.get('example'):
        msg += f'\n📝 {word["example"]}'
    return msg


def format_choice_wrong(*, picked: dict[str, Any], correct: dict[str, Any]) -> str:
    picked_en = picked.get('english') or '?'
    picked_ru = picked.get('translation') or ''
    msg = f'❌ <b>{picked_en}</b>'
    if picked_ru:
        msg += f' — {picked_ru}'
    msg += (
        f'\n\n✅ Нужно: <b>{correct["english"]}</b> — {correct["translation"]}'
    )
    if correct.get('example'):
        msg += f'\n📝 {correct["example"]}'
    return msg


def format_translation_choice_wrong(
    *,
    picked: str,
    correct: dict[str, Any],
    pool: list[dict[str, Any]],
) -> str:
    picked_word = next(
        (w for w in pool if (w.get('translation') or '').strip() == picked.strip()),
        None,
    )
    msg = f'❌ «{picked}»'
    if picked_word:
        msg += f' — это <b>{picked_word["english"]}</b>'
    msg += (
        f'\n\n✅ Нужно: <b>{correct["english"]}</b> — {correct["translation"]}'
    )
    if correct.get('example'):
        msg += f'\n📝 {correct["example"]}'
    return msg


def format_recall_correct(word: dict[str, Any], *, heard: str = '') -> str:
    msg = format_choice_correct(word)
    if heard and heard.strip():
        msg += f'\n(услышал: «{heard.strip()}»)'
    return msg


def format_recall_wrong(word: dict[str, Any], *, heard: str = '') -> str:
    msg = format_choice_wrong(
        picked={'english': heard or '?', 'translation': ''},
        correct=word,
    )
    return msg
