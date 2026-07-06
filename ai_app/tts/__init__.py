"""Text-to-speech layer.

    from ai_app.tts import get_tts_provider, TTSResult
"""

from .base import TTSProvider, TTSResult
from .registry import get_tts_provider

__all__ = ['TTSProvider', 'TTSResult', 'get_tts_provider']
