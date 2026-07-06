"""Provider factory. Selects the AI backend from settings.AI_PROVIDER."""

from __future__ import annotations

from django.conf import settings

from .base import AIProvider
from .mock_provider import MockProvider


# Any OpenAI-style chat-completions endpoint (OpenAI itself, or a gateway such
# as the configured dataeyes.ai proxy) is served by the same provider class.
_OPENAI_COMPATIBLE = {'openai', 'openai_compatible', 'openai-compatible', 'compatible'}


def get_provider(name: str | None = None) -> AIProvider:
    provider = (name or settings.AI_PROVIDER or 'mock').lower()

    if provider in _OPENAI_COMPATIBLE:
        # Imported lazily so the app still boots without httpx/config issues.
        from .openai_provider import OpenAIError, OpenAIProvider

        try:
            return OpenAIProvider()
        except OpenAIError:
            return MockProvider()

    return MockProvider()
