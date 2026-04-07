from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes import incidents as incidents_route
from app.api.schemas.incidents import IncidentAnalyzeRequest
from app.services.exceptions import IncidentAnalysisError


class _FakeCache:
    def __init__(self, seed: dict[str, dict] | None = None) -> None:
        self._store = seed or {}
        self.set_calls = 0

    def get_json(self, key: str):
        return self._store.get(key)

    def set_json(self, key: str, payload: dict, ttl_seconds: int) -> None:
        self._store[key] = payload
        self.set_calls += 1


def test_incidents_route_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_result = SimpleNamespace(
        query="payment failures",
        root_cause="Root cause: database saturation.",
        analyzed_log_ids=[1, 2],
        analyzed_log_count=2,
    )

    monkeypatch.setattr(
        incidents_route,
        "analyze_incident",
        lambda db, query, top_k: fake_result,
    )
    monkeypatch.setattr(incidents_route, "get_cache_client", lambda: None)

    payload = IncidentAnalyzeRequest(query="payment failures", top_k=3)
    result = incidents_route.analyze_incident_route(payload=payload, db=SimpleNamespace())

    assert result.query == "payment failures"
    assert result.root_cause.startswith("Root cause")
    assert result.analyzed_log_ids == [1, 2]
    assert result.analyzed_log_count == 2


def test_incidents_route_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(db, query, top_k):
        raise IncidentAnalysisError("incident_analysis_llm_failed")

    monkeypatch.setattr(incidents_route, "analyze_incident", _raise)
    monkeypatch.setattr(incidents_route, "get_cache_client", lambda: None)

    payload = IncidentAnalyzeRequest(query="payment failures", top_k=3)

    with pytest.raises(HTTPException) as exc:
        incidents_route.analyze_incident_route(payload=payload, db=SimpleNamespace())

    assert exc.value.status_code == 500
    assert exc.value.detail == "Incident analysis failed"


def test_incidents_route_uses_cache_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cache = _FakeCache(
        seed={
            "incident": {
                "query": "payment failures",
                "root_cause": "Root cause: cached response",
                "analyzed_log_ids": [9],
                "analyzed_log_count": 1,
            }
        }
    )

    monkeypatch.setattr(incidents_route, "build_cache_key", lambda *args, **kwargs: "incident")
    monkeypatch.setattr(incidents_route, "get_cache_client", lambda: fake_cache)
    monkeypatch.setattr(incidents_route, "analyze_incident", lambda *args, **kwargs: None)

    payload = IncidentAnalyzeRequest(query="payment failures", top_k=3)
    result = incidents_route.analyze_incident_route(payload=payload, db=SimpleNamespace())

    assert result.root_cause == "Root cause: cached response"
    assert result.analyzed_log_ids == [9]


def test_incidents_route_caches_on_first_call(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cache = _FakeCache()
    calls = {"count": 0}

    def _fake_analyze(db, query, top_k):
        calls["count"] += 1
        return SimpleNamespace(
            query=query,
            root_cause="Root cause: db saturation",
            analyzed_log_ids=[1, 2],
            analyzed_log_count=2,
        )

    monkeypatch.setattr(incidents_route, "build_cache_key", lambda *args, **kwargs: "incident")
    monkeypatch.setattr(incidents_route, "get_cache_client", lambda: fake_cache)
    monkeypatch.setattr(incidents_route, "analyze_incident", _fake_analyze)

    payload = IncidentAnalyzeRequest(query="payment failures", top_k=3)
    first = incidents_route.analyze_incident_route(payload=payload, db=SimpleNamespace())
    second = incidents_route.analyze_incident_route(payload=payload, db=SimpleNamespace())

    assert first.analyzed_log_count == 2
    assert second.analyzed_log_count == 2
    assert calls["count"] == 1
    assert fake_cache.set_calls == 1
