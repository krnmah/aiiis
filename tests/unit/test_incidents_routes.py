from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes import incidents as incidents_route
from app.api.schemas.incidents import IncidentAnalyzeRequest
from app.services.exceptions import IncidentAnalysisError


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

    payload = IncidentAnalyzeRequest(query="payment failures", top_k=3)

    with pytest.raises(HTTPException) as exc:
        incidents_route.analyze_incident_route(payload=payload, db=SimpleNamespace())

    assert exc.value.status_code == 500
    assert exc.value.detail == "Incident analysis failed"
