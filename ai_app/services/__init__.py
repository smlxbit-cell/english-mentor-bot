"""AI service layer for English Mentor Bot.

Public API used by the bot / views:
    from ai_app.services import AnswerChecker, DialoguePartner, get_provider
    from ai_app.services import ChatMessage, CheckResult
"""

from .base import AIProvider
from .checker import AnswerChecker, extract_best_word_match, normalize, score_speaking, score_word_review
from .dialogue import DialoguePartner
from .grammar import explain as explain_grammar, is_garbage_transcript
from .personalize import generate_practice
from .registry import get_provider
from .tutor import EnglishTutor, tutor
from .types import ChatMessage, ChatResult, CheckResult

__all__ = [
    'AIProvider',
    'AnswerChecker',
    'DialoguePartner',
    'EnglishTutor',
    'ChatMessage',
    'ChatResult',
    'CheckResult',
    'explain_grammar',
    'is_garbage_transcript',
    'generate_practice',
    'get_provider',
    'tutor',
    'extract_best_word_match',
    'normalize',
    'score_speaking',
    'score_word_review',
]
