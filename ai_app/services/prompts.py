"""Prompt templates. Kept short on purpose to minimise token spend.

Feedback is returned in Russian (audience = Russian speakers), corrections in
English. AI answers must be strict JSON so parsing is cheap and reliable.
"""

from __future__ import annotations

from .types import ChatMessage

LEVEL_NAMES = {
    'a1': 'A1 (Beginner)',
    'a2': 'A2 (Pre-Intermediate)',
    'b1': 'B1 (Intermediate)',
    'b2': 'B2 (Upper-Intermediate)',
    'c1': 'C1 (Advanced)',
}


CHECK_SYSTEM = (
    'You are an English tutor for Russian-speaking learners. '
    'Evaluate the learner answer briefly. Reply ONLY with compact JSON:\n'
    '{"is_correct": bool, "score": 0..1, "feedback_ru": str, '
    '"correction": str, "tip_ru": str}\n'
    'feedback_ru and tip_ru are in Russian and SHORT (max ~20 words). '
    'correction = a corrected English version (empty if already correct). '
    'Be encouraging. Do not add anything outside JSON.'
)


def build_check_messages(
    *,
    task_prompt: str,
    user_answer: str,
    level: str = 'a2',
    expected: str = '',
    extra_instruction: str = '',
) -> list[ChatMessage]:
    level_name = LEVEL_NAMES.get(level, level.upper())
    parts = [
        f'Learner level: {level_name}.',
        f'Task: {task_prompt}',
    ]
    if expected:
        parts.append(f'Reference/expected answer: {expected}')
    if extra_instruction:
        parts.append(f'Checking notes: {extra_instruction}')
    parts.append(f'Learner answer: {user_answer}')

    return [
        ChatMessage('system', CHECK_SYSTEM),
        ChatMessage('user', '\n'.join(parts)),
    ]


def build_dialogue_system(
    *,
    character_name: str,
    character_role: str,
    personality: str,
    speaking_style: str,
    level: str,
    situation: str,
) -> ChatMessage:
    level_name = LEVEL_NAMES.get(level, level.upper())
    content = (
        f'You are {character_name}, {character_role or "a friendly English speaker"}. '
        f'Personality: {personality or "warm and encouraging"}. '
        f'Speaking style: {speaking_style or "simple, natural"}. '
        f'You are chatting with a Russian learner at level {level_name}. '
        f'Situation: {situation}. '
        'Rules: reply in English only, 1-2 short sentences, use vocabulary the '
        'learner can understand, gently keep the conversation going with a '
        'simple question. If the learner makes a clear mistake, model the '
        'correct form naturally without lecturing.'
    )
    return ChatMessage('system', content)
