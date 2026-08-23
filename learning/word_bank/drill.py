"""Word training drill: listen → meaning → recall (new words); recall-only for SRS."""

from __future__ import annotations

import random
from typing import Any

STEPS_NEW = ('listen', 'meaning', 'recall')
STEPS_REVIEW = ('recall',)

STEP_LABELS = {
    'listen': '🔊 на слух',
    'meaning': '🇬🇧→🇷🇺',
    'recall': '🇷🇺→🇬🇧',
}


def steps_for(*, new_words: bool) -> tuple[str, ...]:
    return STEPS_NEW if new_words else STEPS_REVIEW


def step_label(step: str) -> str:
    return STEP_LABELS.get(step, step)


def _unique_words(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for w in words:
        key = (w.get('english') or '').lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(w)
    return out


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
    return f'✅ <b>Знаю {known_count}</b> · <b>учить {learn_count}</b> → практика'


def format_drill_header(*, word_pos: int, word_total: int, step: str) -> str:
    return f'🎯 <b>{word_pos}/{word_total}</b> · {step_label(step)}'


def format_drill_listen_prompt(header: str) -> str:
    return f'{header}\n\nЧто услышали?'


def format_drill_meaning_prompt(header: str, english: str) -> str:
    return f'{header}\n\n🇬🇧 <b>{english}</b>\n\nВыберите перевод:'


def format_drill_recall_prompt(header: str, translation: str) -> str:
    return (
        f'{header}\n\n'
        f'🇷🇺 «{translation}»\n'
        '✍️ Напишите · 🎙️ Скажите'
    )


def format_choice_correct(word: dict[str, Any]) -> str:
    return f'✅ <b>{word["english"]}</b> — {word["translation"]}'


def format_choice_wrong(*, picked: dict[str, Any], correct: dict[str, Any]) -> str:
    picked_en = picked.get('english') or picked.get('translation') or '?'
    picked_ru = picked.get('translation') or ''
    line = f'❌ «{picked_en}»'
    if picked_ru:
        line += f' — {picked_ru}'
    return (
        f'{line}\n\n'
        f'✅ Нужно: <b>{correct["english"]}</b> — {correct["translation"]}'
    )


def format_translation_choice_wrong(*, picked: str, correct: dict[str, Any]) -> str:
    return (
        f'❌ «{picked}»\n\n'
        f'✅ <b>{correct["english"]}</b> — {correct["translation"]}'
    )


def format_recall_correct(word: dict[str, Any], *, heard: str = '') -> str:
    msg = f'✅ <b>{word["english"]}</b>'
    if heard and heard.strip():
        msg += f'\n(услышал: «{heard.strip()}»)'
    return msg


def format_recall_wrong(word: dict[str, Any], *, heard: str = '') -> str:
    msg = f'❌ <b>{word["english"]}</b> — {word["translation"]}'
    if heard and heard.strip():
        msg += f'\n(было: «{heard.strip()}»)'
    return msg
