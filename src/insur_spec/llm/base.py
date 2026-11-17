from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class EnterpriseProviderInterface(ABC):
    """Abstract interface defining non-leaking, compliant LLM generation for enterprise insurance."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instructions: str = "",
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        """Synchronous completion."""
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        system_instructions: str = "",
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Asynchronous streaming completion."""
        pass
