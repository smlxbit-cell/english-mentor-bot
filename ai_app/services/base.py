"""AI provider abstraction so the concrete backend is swappable.

The rest of the app depends only on this interface, never on OpenAI directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from .types import ChatMessage, ChatResult


class AIProvider(ABC):
    name: str = 'base'

    @abstractmethod
    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> ChatResult:
        """Send a chat completion request and return the assistant text."""
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release any underlying resources (HTTP clients, etc.)."""
        return None
