"""Speech-to-text layer.

    from ai_app.speech import get_stt_provider, Transcript
"""

from .base import STTProvider, Transcript
from .registry import get_stt_provider

__all__ = ['STTProvider', 'Transcript', 'get_stt_provider']
