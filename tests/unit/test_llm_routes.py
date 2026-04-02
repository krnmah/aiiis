from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.routes import llm as llm_route
from app.api.schemas.llm import LLMGenerateRequest
from app.services.exceptions import LLMProviderError


def test_llm_test_route_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_route, "generate_with_local_llm", lambda **kwargs: "ok")

    payload = LLMGenerateRequest(prompt="say hi", model="llama3.2:3b")
    result = llm_route.test_local_llm(payload)

    assert result.model == "llama3.2:3b"
    assert result.response == "ok"


def test_llm_test_route_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(**kwargs):
        raise LLMProviderError("ollama_request_failed")

    monkeypatch.setattr(llm_route, "generate_with_local_llm", _raise)

    payload = LLMGenerateRequest(prompt="say hi")

    with pytest.raises(HTTPException) as exc:
        llm_route.test_local_llm(payload)

    assert exc.value.status_code == 503
    assert exc.value.detail == "Local LLM request failed"
