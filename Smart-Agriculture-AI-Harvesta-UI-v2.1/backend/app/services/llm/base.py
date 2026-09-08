"""
Base LLM Provider Interface.
Defines abstract contracts for AI chat providers (Ollama, self-hosted, cloud API).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMProviderError(Exception):
    """Raised when an LLM provider request fails, times out, or returns an error."""
    pass


class LLMProvider(ABC):
    """
    Abstract interface for large language model providers.
    Allows seamlessly swapping between local Ollama, self-hosted endpoints, or hosted APIs.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the provider name (e.g. 'ollama', 'openai', 'custom')."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Returns the configured model name (e.g. 'qwen2.5-coder:7b')."""
        pass

    @abstractmethod
    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes a chat completion request.
        :param messages: List of {"role": "system"|"user"|"assistant", "content": str}
        :param temperature: Sampling temperature (0.0 to 1.0)
        :param max_tokens: Maximum tokens to generate
        :return: Dict containing {"content": str, "model": str, "usage": Optional[dict]}
        """
        pass
