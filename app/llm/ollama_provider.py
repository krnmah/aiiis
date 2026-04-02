import logging

import httpx

from app.core.config import get_settings
from app.llm.base_provider import BaseLLMProvider
from app.services.exceptions import LLMProviderError

logger = logging.getLogger("app.llm.ollama")


class OllamaProvider(BaseLLMProvider):
    # this provider sends prompt requests to local ollama http api.
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._default_model = settings.ollama_model
        self._timeout_seconds = settings.ollama_timeout_seconds

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        selected_model = model or self._default_model

        payload: dict[str, object] = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = httpx.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("ollama_request_failed", extra={"model": selected_model})
            raise LLMProviderError("ollama_request_failed") from exc

        body = response.json()
        text = body.get("response")
        if not isinstance(text, str) or not text.strip():
            logger.error("ollama_empty_response", extra={"model": selected_model})
            raise LLMProviderError("ollama_empty_response")

        logger.info("ollama_request_succeeded", extra={"model": selected_model})
        return text.strip()
