"""
LLM Provider Factory.
Provides centralized resolver for local Ollama and future hosted AI providers.
"""

import os
from typing import Optional
from backend.app.services.llm.base import LLMProvider, LLMProviderError
from backend.app.services.llm.ollama_provider import OllamaProvider

_active_provider: Optional[LLMProvider] = None


def get_llm_provider(force_new: bool = False) -> LLMProvider:
    """
    Returns the configured LLM provider instance (singleton by default).
    Defaults to local Ollama.
    """
    global _active_provider
    if _active_provider is None or force_new:
        provider_type = os.getenv("AI_PROVIDER", "ollama").lower().strip()
        if provider_type == "ollama":
            _active_provider = OllamaProvider()
        else:
            # Fallback to Ollama if unrecognized
            _active_provider = OllamaProvider()
    return _active_provider


def set_llm_provider(provider: LLMProvider):
    """Overrides the active LLM provider (useful for unit testing / mocking)."""
    global _active_provider
    _active_provider = provider
