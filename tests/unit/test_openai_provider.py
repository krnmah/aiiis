from types import SimpleNamespace

import httpx
import pytest

from app.llm.openai_provider import OpenAIProvider
from app.services.exceptions import LLMProviderError


def test_openai_provider_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": "hello from openai"}}]},
    )
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: fake_response)

    provider = OpenAIProvider()
    provider._api_key = "key"
    text = provider.generate(prompt="hello")

    assert text == "hello from openai"


def test_openai_provider_missing_api_key() -> None:
    provider = OpenAIProvider()
    provider._api_key = None

    with pytest.raises(LLMProviderError, match="openai_missing_api_key"):
        provider.generate(prompt="hello")


def test_openai_provider_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args, **kwargs):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr(httpx, "post", _raise)

    provider = OpenAIProvider()
    provider._api_key = "key"

    with pytest.raises(LLMProviderError, match="openai_request_failed"):
        provider.generate(prompt="hello")


def test_openai_provider_http_401_maps_to_auth_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeOpenAIError(Exception):
        def __init__(self) -> None:
            super().__init__("401 Unauthorized")
            self.response = SimpleNamespace(status_code=401)

    def _raise(*args, **kwargs):
        raise FakeOpenAIError()

    monkeypatch.setattr(httpx, "post", _raise)

    provider = OpenAIProvider()
    provider._api_key = "key"

    with pytest.raises(LLMProviderError, match="openai_auth_failed"):
        provider.generate(prompt="hello")


def test_openai_provider_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": ""}}]},
    )
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: fake_response)

    provider = OpenAIProvider()
    provider._api_key = "key"

    with pytest.raises(LLMProviderError, match="openai_empty_response"):
        provider.generate(prompt="hello")


def test_openai_provider_http_404_maps_to_model_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeOpenAIError(Exception):
        def __init__(self) -> None:
            super().__init__("404 Not Found")
            self.response = SimpleNamespace(status_code=404)

    def _raise(*args, **kwargs):
        raise FakeOpenAIError()

    monkeypatch.setattr(httpx, "post", _raise)

    provider = OpenAIProvider()
    provider._api_key = "key"

    with pytest.raises(LLMProviderError, match="openai_model_not_found"):
        provider.generate(prompt="hello")


def test_openai_provider_retries_on_429_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeOpenAIRateLimitError(Exception):
        def __init__(self) -> None:
            super().__init__("429 Too Many Requests")
            self.response = SimpleNamespace(status_code=429)

    calls = {"count": 0}

    def _post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise FakeOpenAIRateLimitError()
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": "retry success"}}]},
        )

    monkeypatch.setattr(httpx, "post", _post)
    monkeypatch.setattr("app.llm.openai_provider.time.sleep", lambda *_args: None)

    provider = OpenAIProvider()
    provider._api_key = "key"
    provider._retry_attempts = 2
    provider._retry_backoff_seconds = 0

    text = provider.generate(prompt="hello")

    assert calls["count"] == 2
    assert text == "retry success"
