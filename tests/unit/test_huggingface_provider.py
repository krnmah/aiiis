from types import SimpleNamespace

import httpx
import pytest

from app.llm.huggingface_provider import HuggingFaceProvider
from app.services.exceptions import LLMProviderError


def test_huggingface_provider_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": "hello from hf"}}]},
    )
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: fake_response)

    provider = HuggingFaceProvider()
    provider._token = "token"
    text = provider.generate(prompt="hello")

    assert text == "hello from hf"


def test_huggingface_provider_missing_token() -> None:
    provider = HuggingFaceProvider()
    provider._token = None

    with pytest.raises(LLMProviderError, match="huggingface_missing_api_token"):
        provider.generate(prompt="hello")


def test_huggingface_provider_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args, **kwargs):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr(httpx, "post", _raise)

    provider = HuggingFaceProvider()
    provider._token = "token"

    with pytest.raises(LLMProviderError, match="huggingface_request_failed"):
        provider.generate(prompt="hello")


def test_huggingface_provider_http_401_maps_to_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHFError(Exception):
        def __init__(self) -> None:
            super().__init__("401 Unauthorized")
            self.response = SimpleNamespace(status_code=401)

    def _raise(*args, **kwargs):
        raise FakeHFError()

    monkeypatch.setattr(httpx, "post", _raise)

    provider = HuggingFaceProvider()
    provider._token = "token"

    with pytest.raises(LLMProviderError, match="huggingface_auth_failed"):
        provider.generate(prompt="hello")


def test_huggingface_provider_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": ""}}]},
    )
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: fake_response)

    provider = HuggingFaceProvider()
    provider._token = "token"

    with pytest.raises(LLMProviderError, match="huggingface_empty_response"):
        provider.generate(prompt="hello")


def test_huggingface_provider_http_404_maps_to_model_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHFError(Exception):
        def __init__(self) -> None:
            super().__init__("404 Not Found")
            self.response = SimpleNamespace(status_code=404)

    def _raise(*args, **kwargs):
        raise FakeHFError()

    monkeypatch.setattr(httpx, "post", _raise)

    provider = HuggingFaceProvider()
    provider._token = "token"

    with pytest.raises(LLMProviderError, match="huggingface_model_not_found"):
        provider.generate(prompt="hello")
