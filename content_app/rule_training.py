"""Generate short exercise sets to train one grammar rule."""

from __future__ import annotations

import random
import re

_SKIP_GAP = frozenset({
    'i', 'a', 'an', 'the', 'is', 'am', 'are', 'was', 'were', 'be', 'to', 'my', 'your',
    'me', 'you', 'he', 'she', 'it', 'we', 'they', 'and', 'or', 'in', 'on', 'at',
})


def _examples(rule: dict) -> list[dict]:
    out = []
    for ex in rule.get('examples') or []:
        if isinstance(ex, dict) and (ex.get('en') or '').strip():
            out.append(ex)
    return out


def _pick_gap_word(sentence: str) -> str | None:
    words = re.findall(r"[A-Za-z']+", sentence)
    for word in words:
        if word.lower() not in _SKIP_GAP and len(word) >= 3:
            return word
    return words[-1] if words else None


def _gap_options(correct: str, rule: dict) -> list[str]:
    opts = [correct]
    for ex in _examples(rule)[1:4]:
        for word in re.findall(r"[A-Za-z']+", ex['en']):
            if word.lower() not in _SKIP_GAP and word not in opts:
                opts.append(word)
            if len(opts) >= 4:
                break
    for row in (rule.get('table') or {}).get('rows') or []:
        for cell in row:
            for word in re.findall(r"[A-Za-z']+", str(cell)):
                if word.lower() not in _SKIP_GAP and word not in opts:
                    opts.append(word)
                if len(opts) >= 4:
                    break
    while len(opts) < 4:
        opts.append(f'word{len(opts)}')
    random.shuffle(opts)
    return opts[:4]


def build_rule_training_exercises(rule: dict) -> list[dict]:
    """3–4 exercises: MC example, MC gap, typed gap, word order (when possible)."""
    examples = _examples(rule)
    if not examples:
        return []

    title = rule.get('title') or 'Правило'
    correct_en = examples[0]['en'].strip()
    exercises: list[dict] = []

    distractors = [ex['en'].strip() for ex in examples[1:4]]
    for row in (rule.get('table') or {}).get('rows') or []:
        for cell in row:
            cell = str(cell).strip()
            if cell and cell != correct_en and len(cell) > 8 and cell not in distractors:
                distractors.append(cell)
    options = [correct_en]
    for d in distractors:
        if d not in options and len(options) < 4:
            options.append(d)
    random.shuffle(options)
    exercises.append({
        'exercise_type': 'multiple_choice',
        'prompt_ru': f'📘 «{title}»\n\nВыбери верный пример на английском:',
        'options': options,
        'correct': [correct_en],
    })

    gap = _pick_gap_word(correct_en)
    if gap:
        blanked = re.sub(
            re.escape(gap), '___', correct_en, count=1, flags=re.IGNORECASE,
        )
        gap_opts = _gap_options(gap, rule)
        exercises.append({
            'exercise_type': 'multiple_choice',
            'prompt_ru': f'📘 «{title}»\n\nВыбери слово для пропуска:\n\n{blanked}',
            'options': gap_opts,
            'correct': [gap],
        })
        exercises.append({
            'exercise_type': 'fill_gap',
            'prompt_ru': (
                f'📘 «{title}»\n\n✍️ Напиши пропущенное слово '
                f'(или скажи голосом 🎙️):\n\n{blanked}'
            ),
            'correct': [gap],
            'accept_voice': True,
        })

    words = re.findall(r"[A-Za-z']+", correct_en)
    if 4 <= len(words) <= 9:
        bank = words[:]
        random.shuffle(bank)
        target = re.sub(r'[^\w\s]', '', correct_en.lower()).strip()
        exercises.append({
            'exercise_type': 'word_order',
            'prompt_ru': (
                f'📘 «{title}»\n\n🔤 Составь предложение из слов '
                f'(напиши целиком):\n\n{" / ".join(bank)}'
            ),
            'word_bank': bank,
            'correct': [target],
        })

    return exercises[:4]
