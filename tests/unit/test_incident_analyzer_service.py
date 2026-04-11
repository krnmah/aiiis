from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import incident_analyzer_service
from app.services.exceptions import (
    IncidentAnalysisError,
    IngestionPipelineError,
    LLMProviderError,
)


def test_build_incident_prompt_with_logs() -> None:
    fake_log = SimpleNamespace(
        id=10,
        service_name="payments",
        level="ERROR",
        message="timeout from upstream",
        trace_id="trace-10",
        timestamp=datetime.now(timezone.utc),
    )

    prompt = incident_analyzer_service._build_incident_prompt(
        query="payment failures",
        similar_logs=[(fake_log, 0.92)],
    )

    assert "Incident query:" in prompt
    assert "payment failures" in prompt
    assert "log_id=10" in prompt
    assert "timestamp=" in prompt
    assert "service=payments" in prompt
    assert "similarity=0.920" in prompt
    assert "ROOT_CAUSE:" in prompt
    assert "CONFIDENCE:" in prompt


def test_analyze_incident_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_log_a = SimpleNamespace(
        id=1,
        service_name="orders",
        level="ERROR",
        message="db timeout",
        trace_id="trace-1",
        timestamp=datetime.now(timezone.utc),
    )
    fake_log_b = SimpleNamespace(
        id=2,
        service_name="payments",
        level="WARNING",
        message="retry attempts exceeded",
        trace_id=None,
        timestamp=datetime.now(timezone.utc),
    )

    monkeypatch.setattr(
        incident_analyzer_service,
        "find_similar_logs_by_query",
        lambda db, query, top_k: [(fake_log_a, 0.88), (fake_log_b, 0.71)],
    )

    captured: dict[str, str] = {}

    def _fake_generate(
        prompt: str, system_prompt: str | None = None, model: str | None = None
    ) -> str:
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt or ""
        return "Root cause: database saturation caused cascading retries."

    monkeypatch.setattr(
        incident_analyzer_service, "generate_with_local_llm", _fake_generate
    )

    result = incident_analyzer_service.analyze_incident(
        db=MagicMock(),
        query="payment failures",
        top_k=3,
    )

    assert "payment failures" in captured["prompt"]
    assert "db timeout" in captured["prompt"]
    assert "SRE incident analyzer" in captured["system_prompt"]
    assert result.query == "payment failures"
    assert result.root_cause.startswith("Root cause:")
    assert result.analyzed_log_ids == [1, 2]
    assert result.analyzed_log_count == 2


def test_analyze_incident_retrieval_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_retrieval(db, query, top_k):
        raise IngestionPipelineError("query_embedding_generation_failed")

    monkeypatch.setattr(
        incident_analyzer_service, "find_similar_logs_by_query", _raise_retrieval
    )

    with pytest.raises(IncidentAnalysisError, match="incident_log_retrieval_failed"):
        incident_analyzer_service.analyze_incident(
            db=MagicMock(),
            query="payment failures",
            top_k=3,
        )


def test_analyze_incident_llm_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_log = SimpleNamespace(
        id=3,
        service_name="checkout",
        level="ERROR",
        message="upstream failed",
        trace_id="trace-3",
        timestamp=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(
        incident_analyzer_service,
        "find_similar_logs_by_query",
        lambda db, query, top_k: [(fake_log, 0.77)],
    )

    def _raise_llm(
        prompt: str, system_prompt: str | None = None, model: str | None = None
    ) -> str:
        raise LLMProviderError("ollama_request_failed")

    monkeypatch.setattr(
        incident_analyzer_service, "generate_with_local_llm", _raise_llm
    )

    with pytest.raises(IncidentAnalysisError, match="incident_analysis_llm_failed"):
        incident_analyzer_service.analyze_incident(
            db=MagicMock(),
            query="payment failures",
            top_k=3,
        )


def test_analyze_incident_empty_llm_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_log = SimpleNamespace(
        id=4,
        service_name="catalog",
        level="ERROR",
        message="connection reset",
        trace_id=None,
        timestamp=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(
        incident_analyzer_service,
        "find_similar_logs_by_query",
        lambda db, query, top_k: [(fake_log, 0.68)],
    )
    monkeypatch.setattr(
        incident_analyzer_service,
        "generate_with_local_llm",
        lambda prompt, system_prompt=None, model=None: "   ",
    )

    with pytest.raises(IncidentAnalysisError, match="incident_analysis_empty_response"):
        incident_analyzer_service.analyze_incident(
            db=MagicMock(),
            query="payment failures",
            top_k=3,
        )


def test_analyze_incident_no_logs_returns_deterministic_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        incident_analyzer_service,
        "find_similar_logs_by_query",
        lambda db, query, top_k: [],
    )

    called = {"llm_called": False}

    def _fake_generate(
        prompt: str, system_prompt: str | None = None, model: str | None = None
    ) -> str:
        called["llm_called"] = True
        return "should not be called"

    monkeypatch.setattr(
        incident_analyzer_service, "generate_with_local_llm", _fake_generate
    )

    result = incident_analyzer_service.analyze_incident(
        db=MagicMock(),
        query="payment failures",
        top_k=3,
    )

    assert called["llm_called"] is False
    assert result.analyzed_log_ids == []
    assert result.analyzed_log_count == 0
    assert "ROOT_CAUSE:" in result.root_cause
    assert "NEXT_CHECKS:" in result.root_cause
