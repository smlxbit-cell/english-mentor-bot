"""Detect tutor follow-ups that refer to earlier sentences in the chat."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ai_app.speech.bilingual import english_portion_for_tutor
from ai_app.services.types import ChatMessage

_META_MARKERS = (
    'explain better', 'explain the sentence', 'explain that sentence',
    'the sentence which i said', 'the sentence that i said',
    'sentence which i said', 'sentence that i said',
    'sentence i said', 'which i said', 'that i said',
    'why should i say', 'why should it be', 'why is it better',
    'more detail', 'in more detail', 'grammar of all',
    'grammar of the', 'grammar of these', 'grammar of that',
    'last sentence', 'previous sentence', 'what you corrected',
    'what you fixed', 'you corrected', 'analyze the grammar',
    'analyse the grammar', 'break down the grammar', 'tell me why',
    'объясни подробнее', 'объясни лучше', 'объясни детальнее',
    'разбери грамматик', 'грамматику этого', 'грамматику этих',
    'грамматику всех', 'последн', 'предыдущ', 'ту фразу', 'эту фразу',
    'это предложение', 'то предложение', 'то, что я сказал',
    'что я сказал', 'почему так', 'почему нужно', 'как правильно сказать',
    'что ты исправил', 'что исправил', 'разобрать предложение',
    'подробнее про', 'детальнее про',
)

_ASSISTANT_GRAMMAR_MARKERS = (
    'грамматика:', 'grammar:', 'лучше:', 'услышал:', 'ещё можно сказать:',
)


def _history_without_current_user(history: Sequence[ChatMessage]) -> list[ChatMessage]:
    hist = list(history)
    if hist and hist[-1].role == 'user':
        return hist[:-1]
    return hist


def _prior_graded_exchange(history: Sequence[ChatMessage]) -> bool:
    for msg in reversed(_history_without_current_user(history)):
        if msg.role != 'assistant':
            continue
        low = (msg.content or '').lower()
        if any(m in low for m in _ASSISTANT_GRAMMAR_MARKERS):
            return True
    return False


def is_grammar_followup_turn(text: str, history: Sequence[ChatMessage]) -> bool:
    """True when the learner asks to explain grammar of an earlier sentence."""
    if not text or not _prior_graded_exchange(history):
        return False
    low = text.lower()
    return any(m in low for m in _META_MARKERS)


def extract_grammar_followup_target(history: Sequence[ChatMessage]) -> str:
    """English sentence from the prior turn to explain in depth."""
    hist = _history_without_current_user(history)
    for msg in reversed(hist):
        if msg.role != 'assistant':
            continue
        plain = re.sub(r'<[^>]+>', '', msg.content or '')
        for pattern in (
            r'Лучше:\s*«([^»]+)»',
            r'✅\s*«([^»]+)»',
            r'Услышал:\s*«([^»]+)»',
            r'Ещё можно сказать:\s*«([^»]+)»',
        ):
            m = re.search(pattern, plain, re.I)
            if m:
                candidate = m.group(1).strip()
                if len(candidate.split()) >= 3:
                    return candidate
    for msg in reversed(hist):
        if msg.role != 'user':
            continue
        en = english_portion_for_tutor(msg.content or '')
        if en and len(en.split()) >= 3:
            return en
    return ''
