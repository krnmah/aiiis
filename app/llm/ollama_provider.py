import logging
import time

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
        self._retry_attempts = max(1, settings.llm_retry_attempts)
        self._retry_backoff_seconds = max(0.0, settings.llm_retry_backoff_seconds)

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
            response = self._post_with_retry(
                selected_model=selected_model,
                payload=payload,
            )
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

    def _post_with_retry(
        self, selected_model: str, payload: dict[str, object]
    ) -> httpx.Response:
        last_exception: httpx.HTTPError | None = None

        for attempt in range(1, self._retry_attempts + 1):
            try:
                response = httpx.post(
                    f"{self._base_url}/api/generate",
                    json=payload,
                    timeout=self._timeout_seconds,
                )
                response.raise_for_status()
                return response
            except httpx.HTTPError as exc:
                last_exception = exc
                if attempt < self._retry_attempts and self._is_retryable_exception(exc):
                    logger.warning(
                        "ollama_retrying_request",
                        extra={"model": selected_model, "attempt": attempt},
                    )
                    time.sleep(self._retry_backoff_seconds * attempt)
                    continue
                break

        if last_exception is not None:
            raise last_exception

        raise LLMProviderError("ollama_request_failed")

    def _is_retryable_exception(self, exc: httpx.HTTPError) -> bool:
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in (429, 500, 502, 503, 504)
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
