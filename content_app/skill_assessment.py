"""In-depth per-skill assessment used after the CEFR level diagnostic.

Goal: measure grammar, vocabulary, reading, listening, writing and speaking
separately so we can *recommend* a practice focus (the user can still override).

Kept as a static, level-tagged bank so it's easy to grow and needs no DB.
Each item:
    skill:   one of SKILLS
    level:   'a1'..'c1'
    type:    'mc' | 'listening' | 'writing' | 'speaking'
    prompt:  question text shown to the user (RU + EN where needed)
    options: list[str]        (mc / listening)
    correct: list[str]        (accepted answers, compared case-insensitively)
    audio_en: str             (listening: English text to voice, hidden)
    keywords: list[str]       (writing / speaking scoring hints)
    model:   str              (speaking: a model answer to compare against)
"""

from __future__ import annotations

ORDER = ['a1', 'a2', 'b1', 'b2', 'c1']

# Text skills get a short adaptive set; speaking gets a couple of voice prompts.
PER_TEXT_SKILL = 4
PER_SPEAKING = 2

SKILL_LABELS_RU = {
    'grammar': 'Грамматика',
    'vocabulary': 'Слова',
    'reading': 'Чтение',
    'listening': 'Аудирование',
    'writing': 'Письмо',
    'speaking': 'Говорение',
}

SKILLS = list(SKILL_LABELS_RU.keys())


def _lvl(code: str) -> int:
    try:
        return ORDER.index((code or 'a2').lower())
    except ValueError:
        return 1


# --------------------------------------------------------------------------- #
# Question bank
# --------------------------------------------------------------------------- #

BANK: list[dict] = [
    # ---- GRAMMAR ----
    dict(skill='grammar', level='a1', type='mc',
         prompt='She ___ a student.',
         options=['is', 'are', 'am'], correct=['is']),
    dict(skill='grammar', level='a1', type='mc',
         prompt='They ___ TV every evening.',
         options=['watch', 'watches', 'watching'], correct=['watch']),
    dict(skill='grammar', level='a2', type='mc',
         prompt='Yesterday I ___ to the cinema.',
         options=['went', 'go', 'goed'], correct=['went']),
    dict(skill='grammar', level='a2', type='mc',
         prompt='There ___ any milk in the fridge.',
         options=["isn't", "aren't", "wasn't"], correct=["isn't"]),
    dict(skill='grammar', level='b1', type='mc',
         prompt='If it rains, we ___ at home.',
         options=['will stay', 'stay', 'would stay'], correct=['will stay']),
    dict(skill='grammar', level='b1', type='mc',
         prompt='I ___ here since 2020.',
         options=['have lived', 'live', 'lived'], correct=['have lived']),
    dict(skill='grammar', level='b2', type='mc',
         prompt='By the time we arrived, the film ___.',
         options=['had already started', 'already started', 'has already started'],
         correct=['had already started']),
    dict(skill='grammar', level='b2', type='mc',
         prompt='The report needs ___ before Friday.',
         options=['to be finished', 'finishing to', 'be finished'],
         correct=['to be finished']),
    dict(skill='grammar', level='c1', type='mc',
         prompt='___ harder, she would have passed.',
         options=['Had she studied', 'If she studied', 'Would she study'],
         correct=['Had she studied']),
    dict(skill='grammar', level='c1', type='mc',
         prompt='Not only ___ late, but he also forgot the files.',
         options=['was he', 'he was', 'he is'], correct=['was he']),

    # ---- VOCABULARY ----
    dict(skill='vocabulary', level='a1', type='mc',
         prompt='Выбери перевод: «яблоко»',
         options=['apple', 'orange', 'table'], correct=['apple']),
    dict(skill='vocabulary', level='a1', type='mc',
         prompt='Выбери перевод: «большой»',
         options=['big', 'small', 'fast'], correct=['big']),
    dict(skill='vocabulary', level='a2', type='mc',
         prompt='Opposite of «cheap»?',
         options=['expensive', 'quiet', 'early'], correct=['expensive']),
    dict(skill='vocabulary', level='a2', type='mc',
         prompt='Выбери слово: «I need to ___ money for a car.»',
         options=['save', 'spend', 'lose'], correct=['save']),
    dict(skill='vocabulary', level='b1', type='mc',
         prompt='Choose the best word: «The train was ___, so I was late.»',
         options=['delayed', 'arrived', 'missed'], correct=['delayed']),
    dict(skill='vocabulary', level='b1', type='mc',
         prompt='«to give up» means:',
         options=['to stop trying', 'to start again', 'to help'],
         correct=['to stop trying']),
    dict(skill='vocabulary', level='b2', type='mc',
         prompt='Choose the best word: «Her argument was ___ and convincing.»',
         options=['coherent', 'coherce', 'cohesion'], correct=['coherent']),
    dict(skill='vocabulary', level='b2', type='mc',
         prompt='«a tight schedule» means it is:',
         options=['very busy', 'very free', 'very short'], correct=['very busy']),
    dict(skill='vocabulary', level='c1', type='mc',
         prompt='Choose the best word: «The evidence ___ the theory.»',
         options=['corroborates', 'complains', 'consists'],
         correct=['corroborates']),
    dict(skill='vocabulary', level='c1', type='mc',
         prompt='«to gloss over something» means to:',
         options=['ignore its difficulties', 'explain it fully', 'repeat it'],
         correct=['ignore its difficulties']),

    # ---- READING ----
    dict(skill='reading', level='a1', type='mc',
         prompt='«Tom has two cats and a dog.»\n\nHow many pets does Tom have?',
         options=['Three', 'Two', 'One'], correct=['Three']),
    dict(skill='reading', level='a2', type='mc',
         prompt='«The shop opens at 9 and closes at 6.»\n\nIs it open at 7 a.m.?',
         options=['No', 'Yes', "We don't know"], correct=['No']),
    dict(skill='reading', level='b1', type='mc',
         prompt='«Although Anna was tired, she finished the project on time.»\n\n'
                'What do we know about Anna?',
         options=['She finished despite being tired', 'She gave up', 'She was late'],
         correct=['She finished despite being tired']),
    dict(skill='reading', level='b2', type='mc',
         prompt='«The policy was well-intentioned but ultimately counterproductive.»\n\n'
                'The writer thinks the policy:',
         options=['had good aims but bad results', 'was perfect', 'was never used'],
         correct=['had good aims but bad results']),
    dict(skill='reading', level='c1', type='mc',
         prompt='«The proposal, while ambitious, glosses over practical hurdles.»\n\n'
                'The writer implies the proposal:',
         options=['ignores real difficulties', 'solves everything', 'is too modest'],
         correct=['ignores real difficulties']),

    # ---- LISTENING (audio_en is voiced; text hidden) ----
    dict(skill='listening', level='a1', type='listening',
         audio_en='My name is Anna. I am from Spain.',
         prompt='Where is she from?',
         options=['Spain', 'France', 'Italy'], correct=['Spain']),
    dict(skill='listening', level='a2', type='listening',
         audio_en='The meeting starts at ten, not at nine.',
         prompt='When does the meeting start?',
         options=['At ten', 'At nine', 'At eleven'], correct=['At ten']),
    dict(skill='listening', level='b1', type='listening',
         audio_en='Could you send me the report by Friday, please?',
         prompt='What does the speaker want?',
         options=['A report by Friday', 'A meeting on Friday', 'A call on Friday'],
         correct=['A report by Friday']),
    dict(skill='listening', level='b2', type='listening',
         audio_en='Despite the delay, the team managed to launch on time.',
         prompt='What happened?',
         options=['They launched on time', 'They cancelled', 'They were late'],
         correct=['They launched on time']),
    dict(skill='listening', level='c1', type='listening',
         audio_en='We should have looped in the client before signing off.',
         prompt='What is the complaint?',
         options=['The client should have been involved earlier',
                  'The client signed the deal', 'The client was present'],
         correct=['The client should have been involved earlier']),

    # ---- WRITING (short free text; graded on the key word/form) ----
    dict(skill='writing', level='a1', type='writing',
         prompt='Напиши по-английски: «Я люблю кофе.»',
         correct=['i like coffee', 'i love coffee'], keywords=['like', 'coffee']),
    dict(skill='writing', level='a2', type='writing',
         prompt='Поставь глагол в прошедшем: «Yesterday she (go) ___ home early.»',
         correct=['went'], keywords=['went']),
    dict(skill='writing', level='b1', type='writing',
         prompt='Заполни пропуск: «I have been waiting ___ two hours.»',
         correct=['for'], keywords=['for']),
    dict(skill='writing', level='b2', type='writing',
         prompt='Перефразируй формально: «to express concern» → «I am writing to ___ '
                'my concern.»',
         correct=['express', 'raise', 'voice'], keywords=['express']),
    dict(skill='writing', level='c1', type='writing',
         prompt='Заполни пропуск (связка): «___ the challenges, the plan succeeded.»',
         correct=['despite', 'notwithstanding'], keywords=['despite']),

    # ---- SPEAKING (voice or text; scored on keywords/model) ----
    dict(skill='speaking', level='a1', type='speaking',
         prompt='🗣️ Скажи по-английски: расскажи, как тебя зовут и откуда ты.\n\n'
                'Например: «My name is… I am from…»',
         model='My name is Alex and I am from Russia.',
         keywords=['name', 'from']),
    dict(skill='speaking', level='b1', type='speaking',
         prompt='🗣️ Ответь голосом: «What did you do last weekend?» (2-3 предложения).',
         model='Last weekend I met friends and watched a film.',
         keywords=['weekend', 'went', 'watched', 'met', 'was', 'played']),
    dict(skill='speaking', level='b2', type='speaking',
         prompt='🗣️ Ответь голосом: «Describe your job or studies and what you like '
                'about it.»',
         model='I work as an engineer and I enjoy solving problems.',
         keywords=['work', 'study', 'because', 'enjoy', 'like']),
]


def _pick_for_skill(skill: str, user_level: str, count: int) -> list[dict]:
    idx = _lvl(user_level)
    items = [dict(it) for it in BANK if it['skill'] == skill]
    items.sort(key=lambda it: (abs(_lvl(it['level']) - idx), _lvl(it['level'])))
    return items[:count]


def build_test(user_level: str) -> list[dict]:
    """Ordered list of items: text skills first, speaking last."""
    queue: list[dict] = []
    for skill in ('grammar', 'vocabulary', 'reading', 'listening', 'writing'):
        queue.extend(_pick_for_skill(skill, user_level, PER_TEXT_SKILL))
    queue.extend(_pick_for_skill('speaking', user_level, PER_SPEAKING))
    return queue


def recommend(scores: dict[str, tuple[int, int]]) -> list[str]:
    """Return weak skills to suggest as focus (worst first, up to 3)."""
    pct: list[tuple[str, float]] = []
    for skill, (correct, total) in scores.items():
        if total <= 0:
            continue
        pct.append((skill, correct / total))
    if not pct:
        return []
    pct.sort(key=lambda x: x[1])
    weak = [s for s, p in pct if p < 0.6]
    if not weak:
        weak = [pct[0][0]]  # nothing clearly weak → suggest the lowest
    return weak[:3]


def score_summary(scores: dict[str, tuple[int, int]]) -> str:
    """Bilingual, emoji breakdown of per-skill mastery."""
    lines = []
    for skill in SKILLS:
        if skill not in scores:
            continue
        correct, total = scores[skill]
        if total <= 0:
            continue
        p = correct / total
        icon = '🟢' if p >= 0.75 else ('🟡' if p >= 0.5 else '🔴')
        lines.append(f'{icon} {SKILL_LABELS_RU[skill]}: {round(p * 100)}%')
    return '\n'.join(lines)
