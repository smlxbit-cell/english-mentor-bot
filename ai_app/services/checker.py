"""Economical answer checker.

Strategy (see docs/PRODUCT_DESIGN.md §4):
  1. Deterministic checks first (0 tokens): options, exact, sequence, keywords.
  2. AI only for open-ended writing / when explicitly requested as a fallback.
  3. Cache AI verdicts; enforce a per-user daily AI budget.
"""

from __future__ import annotations

import dataclasses
import difflib
import json
import re
from collections.abc import Sequence

from django.conf import settings

from . import economy
from .prompts import build_check_messages
from .registry import get_provider
from .types import CheckResult

_PUNCT_RE = re.compile(r"[.,!?;:\"'`»«…]")
_SPACE_RE = re.compile(r'\s+')

# Exercise types that genuinely need AI judgement.
AI_TYPES = {'writing', 'dialogue_simulation'}
# Types that can optionally escalate to AI when deterministic check fails.
AI_FALLBACK_TYPES = {'translation_ru_en', 'translation_en_ru', 'short_answer'}


def normalize(value: str) -> str:
    value = (value or '').strip().lower()
    value = value.replace('’', "'")
    value = _PUNCT_RE.sub('', value)
    value = _SPACE_RE.sub(' ', value)
    return value.strip()


def _as_variants(correct) -> list[str]:
    """Accept correct answers as 'a|b', ['a', 'b'], or {'answers': [...]}"""
    if correct is None:
        return []
    if isinstance(correct, dict):
        correct = correct.get('answers') or correct.get('answer') or ''
    if isinstance(correct, (list, tuple)):
        items = correct
    else:
        items = str(correct).split('|')
    return [normalize(str(i)) for i in items if str(i).strip()]


_FILLER_WORDS = frozenset({
    'a', 'an', 'the', 'its', "it's", 'is', 'um', 'uh', 'er', 'like',
    'word', 'say', 'i', 'my', 'this', 'that', 'please', 'yes', 'no',
    'its', 'im', "i'm", 'oh', 'well', 'so', 'and',
})


def extract_best_word_match(transcript: str, target: str) -> tuple[str, float]:
    """Pick the token in *transcript* that best matches a single-word *target*."""
    target_n = normalize(target)
    if not target_n:
        return '', 0.0

    full = normalize(transcript)
    if full == target_n:
        return full, 1.0
    if full and ' ' not in target_n:
        full_ratio = difflib.SequenceMatcher(None, full, target_n).ratio()
        if full_ratio >= 0.82:
            return full, full_ratio

    tokens = [
        normalize(w)
        for w in re.split(r'[\s,;.!?\-]+', transcript or '')
        if w.strip()
    ]
    tokens = [t for t in tokens if t and t not in _FILLER_WORDS]

    best_word, best_ratio = '', 0.0
    for token in tokens:
        if token == target_n:
            return token, 1.0
        ratio = difflib.SequenceMatcher(None, token, target_n).ratio()
        if ratio > best_ratio:
            best_ratio, best_word = ratio, token

    return best_word, best_ratio


def score_word_review(transcript: str, target: str) -> tuple[bool, str, float]:
    """Grade a spoken (or typed) single-word SRS answer."""
    target_n = normalize(target)
    guess, ratio = extract_best_word_match(transcript, target)
    if not guess:
        guess = normalize(transcript)
        ratio = difflib.SequenceMatcher(None, guess, target_n).ratio() if guess else 0.0
    ok = guess == target_n or ratio >= 0.82
    return ok, guess, ratio


def score_speaking(transcript: str, target: str) -> CheckResult:
    """Score a spoken attempt (STT transcript) against a target phrase.

    Deterministic and free: combines fuzzy similarity with word overlap.
    Lenient on purpose — speaking practice should encourage, not punish.
    """
    if not transcript:
        return CheckResult(
            is_correct=True,
            score=0.5,
            feedback_ru='Записал твою попытку! 🎙️ Так держать.',
            method='speaking_unavailable',
        )

    a, b = normalize(transcript), normalize(target)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    target_words = [w for w in b.split() if w]
    overlap = (
        sum(1 for w in target_words if w in a.split()) / len(target_words)
        if target_words else 0.0
    )
    score = round(0.5 * ratio + 0.5 * overlap, 2)
    ok = score >= 0.6
    return CheckResult(
        is_correct=ok,
        score=score,
        feedback_ru=(
            'Отлично произнесено! 👏' if ok
            else f'Услышал: «{transcript}». Попробуй ещё разок ближе к образцу 🙂'
        ),
        method='speaking',
        details={'ratio': round(ratio, 2), 'overlap': round(overlap, 2)},
    )


def _keyword_coverage(answer: str, keywords: Sequence[str]) -> float:
    norm = normalize(answer)
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if normalize(kw) in norm)
    return hits / len(keywords)


class AnswerChecker:
    def __init__(self, provider=None):
        self._provider = provider

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_provider()
        return self._provider

    async def check(
        self,
        *,
        exercise_type: str,
        user_answer: str,
        correct=None,
        keywords: Sequence[str] | None = None,
        task_prompt: str = '',
        level: str = 'a2',
        ai_fallback: bool = False,
        ai_check_prompt: str = '',
        user_key: str | None = None,
        keyword_threshold: float = 0.6,
    ) -> CheckResult:
        answer = (user_answer or '').strip()
        keywords = list(keywords or [])

        if not answer:
            return CheckResult(
                is_correct=False,
                feedback_ru='Пустой ответ. Попробуй ещё раз 🙂',
                method='empty',
            )

        # ---- Deterministic path (no tokens) --------------------------------
        if exercise_type not in AI_TYPES:
            deterministic = self._check_deterministic(
                exercise_type=exercise_type,
                answer=answer,
                correct=correct,
                keywords=keywords,
                keyword_threshold=keyword_threshold,
            )
            if deterministic is not None:
                should_escalate = (
                    not deterministic.is_correct
                    and ai_fallback
                    and exercise_type in AI_FALLBACK_TYPES
                )
                if not should_escalate:
                    return deterministic

        # ---- AI path (guarded by cache + budget) ---------------------------
        return await self._check_with_ai(
            exercise_type=exercise_type,
            answer=answer,
            correct=correct,
            task_prompt=task_prompt,
            level=level,
            ai_check_prompt=ai_check_prompt,
            user_key=user_key,
        )

    # ------------------------------------------------------------------ #

    def _check_deterministic(
        self,
        *,
        exercise_type,
        answer,
        correct,
        keywords,
        keyword_threshold,
    ) -> CheckResult | None:
        variants = _as_variants(correct)

        if exercise_type in {'multiple_choice', 'true_false', 'matching', 'word_order'}:
            ok = normalize(answer) in variants
            return CheckResult(
                is_correct=ok,
                score=1.0 if ok else 0.0,
                feedback_ru='Верно! 🎯' if ok else 'Не совсем. Посмотри ещё раз.',
                method='options' if exercise_type != 'word_order' else 'sequence',
            )

        if exercise_type in {'fill_gap', 'auto_exact'}:
            norm = normalize(answer)
            ok = norm in variants
            if not ok and variants:
                for variant in variants:
                    if ' ' in variant:
                        continue
                    _, ratio = extract_best_word_match(answer, variant)
                    if ratio >= 0.82:
                        ok = True
                        break
            return CheckResult(
                is_correct=ok,
                score=1.0 if ok else 0.0,
                feedback_ru='Верно! ✅' if ok else 'Почти! Проверь форму слова.',
                correction='' if ok or not variants else variants[0],
                method='exact',
            )

        if keywords:
            coverage = _keyword_coverage(answer, keywords)
            ok = coverage >= keyword_threshold
            return CheckResult(
                is_correct=ok,
                score=round(coverage, 2),
                feedback_ru=(
                    'Отлично, смысл передан! 👍' if ok
                    else 'Мысль понятна, но не хватает ключевых слов.'
                ),
                method='keywords',
                details={'coverage': round(coverage, 2)},
            )

        if variants:
            ok = normalize(answer) in variants
            return CheckResult(
                is_correct=ok,
                score=1.0 if ok else 0.0,
                feedback_ru='Верно! ✅' if ok else 'Не совсем — сравни с образцом.',
                correction='' if ok else variants[0],
                method='exact',
            )

        return None

    async def _check_with_ai(
        self,
        *,
        exercise_type,
        answer,
        correct,
        task_prompt,
        level,
        ai_check_prompt,
        user_key,
    ) -> CheckResult:
        expected = ''
        variants = _as_variants(correct)
        if variants:
            expected = ' / '.join(variants[:3])

        key = economy.cache_key(exercise_type, normalize(answer), expected, level)
        cached = economy.get_cached(key)
        if cached is not None:
            result = CheckResult(**cached)
            result.method = 'cache'
            return result

        if not economy.can_spend(user_key):
            return self._budget_fallback(answer, variants)

        messages = build_check_messages(
            task_prompt=task_prompt or 'Evaluate the learner answer.',
            user_answer=answer,
            level=level,
            expected=expected,
            extra_instruction=ai_check_prompt,
        )

        # Writing/dialogue judgement uses the default model; cheap second-opinion
        # checks (translation/short-answer fallback) use the cheaper model.
        model = (
            settings.OPENAI_MODEL if exercise_type in AI_TYPES
            else settings.OPENAI_CHEAP_MODEL
        )

        try:
            chat = await self.provider.chat(
                messages,
                model=model,
                max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
                temperature=0.2,
                json_mode=True,
            )
        except Exception:  # noqa: BLE001 - never break a lesson on AI error
            return self._budget_fallback(answer, variants)

        economy.register_spend(user_key)
        result = self._parse_ai(chat.text)
        economy.set_cached(key, dataclasses.asdict(result))
        return result

    def _parse_ai(self, text: str) -> CheckResult:
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            match = re.search(r'\{.*\}', text or '', re.DOTALL)
            if not match:
                return CheckResult(
                    is_correct=True,
                    score=0.7,
                    feedback_ru='Принято! (не удалось разобрать ответ AI)',
                    used_ai=True,
                    method='ai',
                )
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = {}

        return CheckResult(
            is_correct=bool(data.get('is_correct', False)),
            score=float(data.get('score', 0.0) or 0.0),
            feedback_ru=str(data.get('feedback_ru', '')).strip(),
            correction=str(data.get('correction', '')).strip(),
            tip_ru=str(data.get('tip_ru', '')).strip(),
            used_ai=True,
            method='ai',
        )

    def _budget_fallback(self, answer, variants) -> CheckResult:
        ok = normalize(answer) in variants if variants else True
        return CheckResult(
            is_correct=ok,
            score=1.0 if ok else 0.5,
            feedback_ru='Ответ принят 🙂 (детальная AI-проверка временно недоступна)',
            method='budget_fallback',
        )
