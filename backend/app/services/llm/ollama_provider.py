"""
Local Ollama LLM Provider.
Communicates directly with the local Ollama HTTP API (http://127.0.0.1:11434/api/chat).
"""

import os
import logging
from typing import List, Dict, Any, Optional
import httpx

from backend.app.services.llm.base import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_TIMEOUT_SECONDS = 30.0


class OllamaProvider(LLMProvider):
    """
    Ollama implementation for local, quota-free agricultural intelligence.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self._base_url = (base_url or os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)).rstrip("/")
        # Prioritize explicit model, then env var if non-empty, then default qwen2.5-coder:7b
        env_model = os.getenv("OLLAMA_MODEL", "").strip()
        self._model = model or (env_model if env_model else DEFAULT_OLLAMA_MODEL)
        configured_timeout = os.getenv("OLLAMA_TIMEOUT_SECONDS", "").strip()
        self._timeout = timeout if timeout is not None else (
            float(configured_timeout) if configured_timeout else DEFAULT_TIMEOUT_SECONDS
        )

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    async def _resolve_installed_model(self, client: httpx.AsyncClient) -> Optional[str]:
        """Queries local Ollama tags to find an installed model if the requested one is missing."""
        try:
            res = await client.get(f"{self._base_url}/api/tags")
            if res.status_code == 200:
                tags = res.json().get("models", [])
                tag_names = [m.get("name", "") for m in tags]
                if "qwen2.5-coder:7b" in tag_names:
                    return "qwen2.5-coder:7b"
                if tag_names:
                    return tag_names[0]
        except Exception:
            pass
        return None

    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Sends chat completion request to local Ollama /api/chat endpoint.
        """
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "keep_alive": "15m",
            "options": {
                "temperature": temperature,
                "num_ctx": 4096,
            },
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        url = f"{self._base_url}/api/chat"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload)

                # If 404 (model not found), attempt fallback to installed model
                if response.status_code == 404 and "not found" in response.text.lower():
                    fallback_model = await self._resolve_installed_model(client)
                    if fallback_model and fallback_model != self._model:
                        logger.info(f"Model '{self._model}' not found on Ollama. Falling back to installed '{fallback_model}'.")
                        payload["model"] = fallback_model
                        response = await client.post(url, json=payload)

            if response.status_code != 200:
                error_body = response.text[:300]
                logger.error(f"Ollama API returned HTTP {response.status_code}: {error_body}")
                raise LLMProviderError(
                    f"Local Ollama error (HTTP {response.status_code}): {error_body or 'Unexpected response.'}"
                )

            data = response.json()
            message_obj = data.get("message", {})
            content = message_obj.get("content", "").strip()

            if not content:
                raise LLMProviderError("Ollama returned an empty response.")

            return {
                "content": content,
                "model": data.get("model", self._model),
                "total_duration": data.get("total_duration"),
                "eval_count": data.get("eval_count"),
            }

        except httpx.ConnectError as conn_err:
            logger.warning(f"Failed to connect to local Ollama at {self._base_url}: {conn_err}")
            raise LLMProviderError(
                f"Local AI assistant is currently unreachable at {self._base_url}. "
                f"Please ensure Ollama is running with model '{self._model}'."
            )
        except httpx.TimeoutException as time_err:
            logger.warning(f"Ollama request timed out after {self._timeout}s: {time_err}")
            raise LLMProviderError(
                f"Local AI assistant request timed out after {int(self._timeout)}s. "
                "The model may still be loading or generating a response."
            )
        except Exception as err:
            if isinstance(err, LLMProviderError):
                raise
            logger.error(f"Unexpected error communicating with Ollama: {err}", exc_info=True)
            raise LLMProviderError(f"Local AI assistant communication failed: {str(err)}")
