"""Map tutor grammar feedback to library rule keys."""

from __future__ import annotations

import re

_RULE_TAG_RE = re.compile(r'\[RULE:([a-z0-9\-,]+)\]\s*$', re.MULTILINE)
_CORRECTION_RE = re.compile(
    r'❌\s*(?P<wrong>[^→\n<]+?)\s*→\s*✅\s*(?P<right>[^→\n<]+)',
)

VALID_RULE_KEYS = frozenset({
    'greetings-hello', 'greetings-goodbye', 'polite-requests', 'thank-you-responses',
    'to-be-basics', 'articles-a-an', 'plural-s', 'present-simple-affirmative',
    'present-simple-questions', 'wh-questions-basics', 'navigation-where',
    'navigation-directions', 'prepositions-place', 'modal-can', 'modal-could-polite',
    'hotel-check-in',
})


def strip_rule_tags(reply: str) -> tuple[str, list[str]]:
    """Remove [RULE:key] footer from tutor reply; return cleaned text + keys."""
    text = (reply or '').strip()
    keys: list[str] = []
    match = _RULE_TAG_RE.search(text)
    if match:
        keys = [
            k.strip() for k in match.group(1).split(',')
            if k.strip() in VALID_RULE_KEYS
        ]
        text = _RULE_TAG_RE.sub('', text).rstrip()
    return text, keys[:2]


def extract_grammar_corrections(tutor_reply: str) -> list[tuple[str, str]]:
    """Parse ❌ wrong → ✅ right pairs from tutor grammar feedback."""
    pairs: list[tuple[str, str]] = []
    for match in _CORRECTION_RE.finditer(tutor_reply or ''):
        wrong = match.group('wrong').strip().strip('«»"\'')
        right = match.group('right').strip().strip('«»"\'')
        if wrong and right:
            pairs.append((wrong, right))
    return pairs


def _normalize_tokens(text: str) -> list[str]:
    return [
        t for t in re.sub(r'[^\w\s]', ' ', (text or '').lower()).split()
        if t
    ]


def is_capitalization_only_mistake(wrong: str, right: str) -> bool:
    """True when wrong/right differ only by letter case."""
    w = _normalize_tokens(wrong)
    r = _normalize_tokens(right)
    if not w or not r or len(w) != len(r):
        return False
    return w == r


def is_substantive_grammar_mistake(wrong: str, right: str) -> bool:
    """False for capitalization / punctuation-only nits."""
    if is_capitalization_only_mistake(wrong, right):
        return False
    w = re.sub(r'\s+', ' ', (wrong or '').strip().lower())
    r = re.sub(r'\s+', ' ', (right or '').strip().lower())
    return w != r


def reply_has_grammar_mistakes(reply: str) -> bool:
    return '❌' in (reply or '') or '→ ✅' in (reply or '')


def reply_has_substantive_grammar_mistakes(reply: str) -> bool:
    """True when tutor flagged a real grammar issue, not just capital I."""
    return any(
        is_substantive_grammar_mistake(w, r)
        for w, r in extract_grammar_corrections(reply)
    )


def _looks_like_vocabulary_substitution(wl: str, rl: str) -> bool:
    """STT turned Russian into nonsense English — not a grammar-rule topic."""
    if re.search(r'\b(read have|readhav|redhav|razvehvati|ragbiet|prodvigat)\b', wl):
        return True
    w_tokens = _normalize_tokens(wl)
    r_tokens = _normalize_tokens(rl)
    if not w_tokens or not r_tokens:
        return False
    overlap = len(set(w_tokens) & set(r_tokens))
    return overlap <= 1 and len(w_tokens) >= 2 and len(r_tokens) >= 1


def _match_correction_to_rule(wrong: str, right: str) -> str | None:
    """Map one correction pair to a library rule, or None if no good fit."""
    wl = wrong.lower()
    rl = right.lower()

    if re.search(r'\b(read have|readhav|thompson|tompson)\b', wl):
        return None

    if re.search(r'\bwhat should i\b', wl) and re.search(r'\bwhat should i\b', rl):
        return None
    if re.search(r'\bhow should i\b', wl) and re.search(r'\bhow should i\b', rl):
        return None

    if re.search(r'\bi want\b', wl) and 'would like' in rl:
        return 'polite-requests'
    if re.search(r'\bgive me\b', wl) and ('could i have' in rl or 'can i have' in rl):
        return 'polite-requests'
    if re.search(r'\bcan i have\b', wl) and re.search(r'\bcan i have\b', rl):
        if wl != rl:
            return 'polite-requests'

    if re.search(r'\b(could you|could i)\b', wl) and re.search(
        r'\b(can you|can i)\b', rl,
    ) and 'could' not in wl:
        return 'modal-could-polite'
    if re.search(r'\bcan\'?t\b', wl) or re.search(r'\bcan\'?t\b', rl):
        if wl != rl:
            return 'modal-can'
    if re.search(r'\bcan (you|i|we|they|he|she)\b', wl) and not re.search(
        r'\bcan (you|i|we|they|he|she)\b', rl,
    ):
        return 'modal-can'
    if re.search(r'\bcan (you|i|we|they|he|she)\b', rl) and not re.search(
        r'\bcan (you|i|we|they|he|she)\b', wl,
    ):
        return 'modal-can'

    if re.search(r'\b(i is|you is|he are|she are|we is|they is)\b', wl):
        return 'to-be-basics'
    if re.search(r'\bi am\b', wl) and re.search(r'\bi (is|are)\b', rl):
        return 'to-be-basics'

    if re.search(r'\ba [aeiou]', wl) or re.search(r'\ban [^aeiouh]', wl):
        if re.search(r'\b(a|an) ', rl):
            return 'articles-a-an'

    if re.search(r'\b(does you|do he|do she|does they|did he|did she)\b', wl):
        return 'present-simple-questions'
    if re.search(r'\bdon\'?t\b', wl) != re.search(r'\bdon\'?t\b', rl):
        return 'present-simple-questions'

    if re.search(r'\bwhat is you\b|\bhow you are\b|\bwhere you are\b', wl):
        return 'wh-questions-basics'

    if re.search(r'\b(in|on|at) (the )?(table|bus|train|hotel|station)\b', wl):
        if re.search(r'\b(in|on|at) (the )?(table|bus|train|hotel|station)\b', rl):
            if wl != rl:
                return 'prepositions-place'

    if re.search(r'\b(hello|hi|good morning|good evening)\b', wl) and wl != rl:
        return 'greetings-hello'
    if re.search(r'\b(bye|goodbye|see you)\b', wl) and wl != rl:
        return 'greetings-goodbye'
    if re.search(r'\b(thank you|thanks)\b', wl) and wl != rl:
        return 'thank-you-responses'

    return None


def infer_rule_keys_from_corrections(corrections: list[tuple[str, str]]) -> list[str]:
    keys: list[str] = []
    for wrong, right in corrections:
        if not is_substantive_grammar_mistake(wrong, right):
            continue
        key = _match_correction_to_rule(wrong, right)
        if key and key not in keys:
            keys.append(key)
    return keys[:1]


def suggest_rule_keys(*, user_text: str, tutor_reply: str, tagged_keys: list[str]) -> list[str]:
    """Rule tablet only when a correction clearly matches a library topic."""
    del user_text  # never match rules from raw learner text — only from corrections

    corrections = extract_grammar_corrections(tutor_reply)
    inferred = infer_rule_keys_from_corrections(corrections)
    if inferred:
        return inferred

    substantive = [
        (w, r) for w, r in corrections
        if is_substantive_grammar_mistake(w, r)
    ]
    if not substantive:
        return []

    if tagged_keys:
        for key in tagged_keys:
            if key not in VALID_RULE_KEYS:
                continue
            for wrong, right in substantive:
                if _match_correction_to_rule(wrong, right) == key:
                    return [key]
    return []
