"""Shared data structures for the AI layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str  # 'system' | 'user' | 'assistant'
    content: str

    def as_dict(self) -> dict:
        return {'role': self.role, 'content': self.content}


@dataclass
class ChatResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ''
    raw: dict | None = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class CheckResult:
    """Result of checking a single learner answer.

    `method` records how the verdict was produced so we can audit token spend:
    'exact' | 'options' | 'keywords' | 'sequence' | 'ai' | 'cache' |
    'budget_fallback' | 'empty'.
    """

    is_correct: bool
    score: float = 0.0  # 0.0 .. 1.0
    feedback_ru: str = ''
    correction: str = ''
    tip_ru: str = ''
    used_ai: bool = False
    method: str = ''
    details: dict = field(default_factory=dict)
