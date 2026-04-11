import logging
import time

import httpx

from app.core.config import get_settings
from app.llm.base_provider import BaseLLMProvider
from app.services.exceptions import LLMProviderError

logger = logging.getLogger("app.llm.openai")


class OpenAIProvider(BaseLLMProvider):
    # provider for openai chat completions requests.
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openai_api_key
        self._default_model = settings.openai_model
        self._chat_url = settings.openai_chat_completions_url
        self._timeout_seconds = settings.openai_timeout_seconds
        self._retry_attempts = max(1, settings.llm_retry_attempts)
        self._retry_backoff_seconds = max(0.0, settings.llm_retry_backoff_seconds)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        if not self._api_key:
            raise LLMProviderError("openai_missing_api_key")

        selected_model = model or self._default_model
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": selected_model,
            "messages": messages,
            "max_tokens": 512,
        }

        try:
            response = self._post_with_retry(
                selected_model=selected_model,
                headers=headers,
                payload=payload,
            )
        except Exception as exc:
            status_code = self._extract_status_code(exc)
            if status_code in (401, 403):
                raise LLMProviderError("openai_auth_failed") from exc
            if status_code == 404:
                raise LLMProviderError("openai_model_not_found") from exc
            if status_code == 429:
                raise LLMProviderError("openai_rate_limited") from exc

            logger.exception("openai_request_failed", extra={"model": selected_model})
            raise LLMProviderError("openai_request_failed") from exc

        body = response.json()
        choices = body.get("choices") if isinstance(body, dict) else None
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

        logger.error("openai_empty_response", extra={"model": selected_model})
        raise LLMProviderError("openai_empty_response")

    @staticmethod
    def _extract_status_code(exc: Exception) -> int | None:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        return status_code if isinstance(status_code, int) else None

    def _post_with_retry(
        self,
        selected_model: str,
        headers: dict[str, str],
        payload: dict[str, object],
    ) -> httpx.Response:
        last_exception: Exception | None = None

        for attempt in range(1, self._retry_attempts + 1):
            try:
                response = httpx.post(
                    self._chat_url,
                    headers=headers,
                    json=payload,
                    timeout=self._timeout_seconds,
                )
                response.raise_for_status()
                return response
            except Exception as exc:  # noqa: BLE001
                last_exception = exc
                if attempt < self._retry_attempts and self._is_retryable_exception(exc):
                    logger.warning(
                        "openai_retrying_request",
                        extra={"model": selected_model, "attempt": attempt},
                    )
                    time.sleep(self._retry_backoff_seconds * attempt)
                    continue
                break

        if last_exception is not None:
            raise last_exception

        raise LLMProviderError("openai_request_failed")

    def _is_retryable_exception(self, exc: Exception) -> bool:
        status_code = self._extract_status_code(exc)
        if status_code in (429, 500, 502, 503, 504):
            return True
        return isinstance(
            exc,
            (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
                httpx.RemoteProtocolError,
            ),
        )
