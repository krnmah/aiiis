from unittest.mock import MagicMock

import httpx
import pytest

from app.llm.ollama_provider import OllamaProvider
from app.services.exceptions import LLMProviderError


def test_ollama_provider_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = MagicMock()
    fake_response.json.return_value = {"response": "hello from ollama"}
    fake_response.raise_for_status.return_value = None

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: fake_response)

    provider = OllamaProvider()
    text = provider.generate(prompt="hello")

    assert text == "hello from ollama"


def test_ollama_provider_generate_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args, **kwargs):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr(httpx, "post", _raise)

    provider = OllamaProvider()

    with pytest.raises(LLMProviderError, match="ollama_request_failed"):
        provider.generate(prompt="hello")


def test_ollama_provider_generate_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = MagicMock()
    fake_response.json.return_value = {"response": ""}
    fake_response.raise_for_status.return_value = None

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: fake_response)

    provider = OllamaProvider()

    with pytest.raises(LLMProviderError, match="ollama_empty_response"):
        provider.generate(prompt="hello")
