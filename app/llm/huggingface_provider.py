import logging

import httpx

from app.core.config import get_settings
from app.llm.base_provider import BaseLLMProvider
from app.services.exceptions import LLMProviderError

logger = logging.getLogger("app.llm.huggingface")


class HuggingFaceProvider(BaseLLMProvider):
    # provider for hugging face inference api model calls.
    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.huggingface_api_token
        self._default_model = settings.huggingface_model
        self._timeout_seconds = settings.huggingface_timeout_seconds
        self._chat_url = settings.huggingface_chat_completions_url

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        if not self._token:
            raise LLMProviderError("huggingface_missing_api_token")

        selected_model = model or self._default_model
        merged_prompt = prompt
        if system_prompt:
            merged_prompt = f"System:\n{system_prompt}\n\nUser:\n{prompt}"

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [{"role": "user", "content": merged_prompt}],
            "model": selected_model,
            "max_tokens": 512,
        }

        try:
            response = httpx.post(
                self._chat_url,
                headers=headers,
                json=payload,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except Exception as exc:
            status_code = self._extract_status_code(exc)
            if status_code in (401, 403):
                raise LLMProviderError("huggingface_auth_failed") from exc
            if status_code == 404:
                raise LLMProviderError("huggingface_model_not_found") from exc
            if status_code == 429:
                raise LLMProviderError("huggingface_rate_limited") from exc

            logger.exception("huggingface_request_failed", extra={"model": selected_model})
            raise LLMProviderError("huggingface_request_failed") from exc

        body = response.json()
        choices = body.get("choices") if isinstance(body, dict) else None
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

        if isinstance(body, dict) and isinstance(body.get("error"), dict):
            logger.error("huggingface_provider_error", extra={"model": selected_model})
            raise LLMProviderError("huggingface_provider_error")

        logger.error("huggingface_empty_response", extra={"model": selected_model})
        raise LLMProviderError("huggingface_empty_response")

    @staticmethod
    def _extract_status_code(exc: Exception) -> int | None:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        return status_code if isinstance(status_code, int) else None
