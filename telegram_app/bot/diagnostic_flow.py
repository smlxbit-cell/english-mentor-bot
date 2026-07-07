"""Adaptive CEFR diagnostic: self-assessment → calibrated test → optional challenge."""

from __future__ import annotations

LEVELS = ['a1', 'a2', 'b1', 'b2']
LEVEL_LABELS = {
    'a1': 'A1 (начальный)',
    'a2': 'A2 (элементарный)',
    'b1': 'B1 (средний)',
    'b2': 'B2 (выше среднего)',
    'unsure': 'Не уверен(а)',
}

PRIMARY_QUESTIONS = 8
CHALLENGE_QUESTIONS = 3
CHALLENGE_MIN_ACCURACY = 0.85


def level_index(code: str) -> int:
    code = (code or 'a2').lower()
    if code == 'unsure':
        return 1
    try:
        return LEVELS.index(code)
    except ValueError:
        return 1


def test_band(claimed: str) -> tuple[int, int, int]:
    """Return (min_idx, max_idx, start_idx) for question pool."""
    idx = level_index(claimed)
    if claimed == 'unsure':
        return 0, 2, 1
    if idx == 0:  # A1 — simple only, no B1/B2 traps
        return 0, 1, 0
    if idx == 1:  # A2
        return 0, 2, 1
    if idx == 2:  # B1
        return 1, 3, 2
    return 2, 3, 3  # B2


def challenge_band(claimed_idx: int, result_idx: int) -> tuple[int, int]:
    """Questions one CEFR step above the primary result."""
    target = min(3, max(result_idx, claimed_idx) + 1)
    return target, target


def pick_item(
    group: dict[str, list],
    asked: set[int],
    band: tuple[int, int],
    focus_idx: int,
    *,
    used_skills: set[str] | None = None,
):
    used_skills = used_skills or set()
    min_i, max_i = band
    focus_idx = max(min_i, min(max_i, focus_idx))
    order = [focus_idx]
    for d in range(1, 4):
        if focus_idx - d >= min_i:
            order.append(focus_idx - d)
        if focus_idx + d <= max_i:
            order.append(focus_idx + d)

    fallback = None
    for idx in order:
        level = LEVELS[idx]
        for it in group.get(level, []):
            if it['id'] in asked:
                continue
            if it['skill'] not in used_skills:
                return it
            if fallback is None:
                fallback = it
    return fallback


def accuracy(correct: int, total: int) -> float:
    return correct / total if total else 0.0


def task_instruction(item: dict) -> str:
    """Short, clear task line so the user knows what to do."""
    itype = item.get('item_type', '')
    if itype in ('multiple_choice', 'listening'):
        prompt = item.get('prompt') or ''
        if '___' in prompt:
            return 'Выбери слово для пропуска 👇'
        if 'перевод' in prompt.lower() or 'по-английски:' in prompt.lower():
            return 'Выбери правильный перевод 👇'
        return 'Выбери правильный вариант 👇'
    if itype == 'fill_gap':
        return 'Напиши пропущенное слово ✍️'
    if itype == 'translation_ru_en':
        return ''  # prompt already says «Переведи на английский»
    if itype == 'speaking':
        return 'Можно текстом или голосовым 🎙️'
    return ''


def should_offer_challenge(diag: dict) -> bool:
    if diag.get('phase') != 'primary_done':
        return False
    correct = diag.get('correct', 0)
    total = diag.get('count', 0)
    if total < PRIMARY_QUESTIONS or accuracy(correct, total) < CHALLENGE_MIN_ACCURACY:
        return False
    result_idx = diag.get('level_idx', 0)
    ceiling = diag['band'][1]
    return result_idx >= ceiling and ceiling < 3


def finalize_level(diag: dict) -> str:
    if diag.get('challenge') or diag.get('phase') == 'challenge_done':
        idx = diag.get('level_idx', 1)
    else:
        idx = max(diag['band'][0], min(diag['band'][1], diag.get('level_idx', 1)))
    if diag.get('phase') == 'challenge_done' and diag.get('challenge_correct', 0) >= 3:
        idx = min(3, idx + 1)
    return LEVELS[idx]


def result_message(claimed: str, level_code: str, diag: dict) -> str:
    level_up = level_index(level_code) > level_index(claimed)
    acc = accuracy(diag.get('correct', 0), max(diag.get('count', 1), 1))
    lvl = level_code.upper()

    if claimed == 'b2' and level_code == 'b2' and acc >= 0.8:
        return (
            f'Отлично! Твой уровень — <b>{lvl}</b> 🎯\n\n'
            'Бот настроен под уверенный B2: интересные истории, живые диалоги '
            'и практика без «детского» английского.\n'
            'Можно и дальше шлифовать нюансы — я помогу.'
        )
    if level_up:
        return (
            f'Ты ответил(а) очень хорошо! Похоже, твой уровень выше, чем ты думал(а).\n\n'
            f'Ставим <b>{lvl}</b> 🎯 — начнём с комфортных заданий, без лишней сложности.'
        )
    if acc < 0.45 and level_index(level_code) <= level_index(claimed):
        return (
            f'Спасибо за честные ответы! Начнём с <b>{lvl}</b> 🎯\n\n'
            'Будем идти маленькими шагами — без сложной грамматики с первого дня.'
        )
    return (
        f'Готово! Твой уровень — <b>{lvl}</b> 🎯\n\n'
        'Подберу уроки так, чтобы было интересно и не раздражало.'
    )
