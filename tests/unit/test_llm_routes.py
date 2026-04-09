from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.routes import llm as llm_route
from app.api.schemas.llm import LLMGenerateRequest
from app.services.exceptions import LLMProviderError


def test_llm_test_route_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_route, "generate_with_local_llm", lambda **kwargs: "ok")
    monkeypatch.setattr(llm_route, "get_default_llm_model", lambda: "google/flan-t5-base")

    payload = LLMGenerateRequest(prompt="say hi", model="llama3.2:3b")
    result = llm_route.test_local_llm(payload)

    assert result.model == "llama3.2:3b"
    assert result.response == "ok"


def test_llm_test_route_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(**kwargs):
        raise LLMProviderError("ollama_request_failed")

    monkeypatch.setattr(llm_route, "generate_with_local_llm", _raise)
    monkeypatch.setattr(llm_route, "get_default_llm_model", lambda: "google/flan-t5-base")

    payload = LLMGenerateRequest(prompt="say hi")

    with pytest.raises(HTTPException) as exc:
        llm_route.test_local_llm(payload)

    assert exc.value.status_code == 503
    assert exc.value.detail == "Local LLM request failed"


def test_llm_model_check_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_route, "generate_with_local_llm", lambda **kwargs: "ok")
    monkeypatch.setattr(llm_route, "get_default_llm_model", lambda: "google/flan-t5-base")

    result = llm_route.check_llm_model(model=None)

    assert result.available is True
    assert result.detail == "model_available"


def test_llm_model_check_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(**kwargs):
        raise LLMProviderError("huggingface_model_not_found")

    monkeypatch.setattr(llm_route, "generate_with_local_llm", _raise)
    monkeypatch.setattr(llm_route, "get_default_llm_model", lambda: "google/flan-t5-base")

    result = llm_route.check_llm_model(model="bad-model")

    assert result.available is False
    assert result.model == "bad-model"
    assert result.detail == "huggingface_model_not_found"
