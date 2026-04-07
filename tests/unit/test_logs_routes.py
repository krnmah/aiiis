from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.routes import logs as logs_route
from app.api.schemas.logs import LogCreateRequest
from app.services.exceptions import IngestionPipelineError


class _FakeCache:
    def __init__(self, seed: dict[str, dict] | None = None) -> None:
        self._store = seed or {}
        self.set_calls = 0

    def get_json(self, key: str):
        return self._store.get(key)

    def set_json(self, key: str, payload: dict, ttl_seconds: int) -> None:
        self._store[key] = payload
        self.set_calls += 1


def test_ingest_log_success(monkeypatch: pytest.MonkeyPatch) -> None:
    # route test uses fake service result to keep scope focused on route mapping.
    fake_log = SimpleNamespace(
        id=10,
        service_name="orders-service",
        level="ERROR",
        message="order failed",
        trace_id="trace-r1",
        timestamp=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(logs_route, "create_log_entry", lambda payload, db: fake_log)

    payload = LogCreateRequest(
        service_name="orders-service",
        level="ERROR",
        message="order failed",
        trace_id="trace-r1",
    )

    result = logs_route.ingest_log(payload=payload, db=MagicMock())

    assert result.id == 10
    assert result.service_name == "orders-service"


def test_ingest_log_maps_pipeline_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_error(payload: LogCreateRequest, db: MagicMock) -> None:
        raise IngestionPipelineError("ingestion_db_write_failed")

    monkeypatch.setattr(logs_route, "create_log_entry", _raise_error)

    payload = LogCreateRequest(
        service_name="orders-service",
        level="ERROR",
        message="order failed",
    )

    with pytest.raises(HTTPException) as exc:
        logs_route.ingest_log(payload=payload, db=MagicMock())

    assert exc.value.status_code == 500
    assert exc.value.detail == "Log ingestion failed"


def test_get_log_embedding_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(logs_route, "get_embedding_for_log", lambda db, log_id: [0.3, 0.4, 0.5])

    response = logs_route.get_log_embedding(log_id=33, include_vector=False, db=MagicMock())

    assert response.log_id == 33
    assert response.embedding_dimension == 3
    assert response.embedding is None


def test_get_log_embedding_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(logs_route, "get_embedding_for_log", lambda db, log_id: None)

    with pytest.raises(HTTPException) as exc:
        logs_route.get_log_embedding(log_id=99, include_vector=True, db=MagicMock())

    assert exc.value.status_code == 404


def test_search_similar_logs_clamps_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, int] = {}
    monkeypatch.setattr(logs_route, "get_cache_client", lambda: None)

    fake_log = SimpleNamespace(
        id=2,
        service_name="checkout",
        level="WARNING",
        message="amount mismatch",
        trace_id=None,
        timestamp=datetime.now(timezone.utc),
    )

    def _fake_find_similar_logs_by_query(db: MagicMock, query: str, top_k: int):
        captured["top_k"] = top_k
        return [(fake_log, 0.91)]

    monkeypatch.setattr(logs_route, "find_similar_logs_by_query", _fake_find_similar_logs_by_query)

    response = logs_route.search_similar_logs(query="amount mismatch", top_k=999, db=MagicMock())

    assert captured["top_k"] == 20
    assert response.total == 1
    assert response.results[0].similarity_score == 0.91


def test_search_similar_logs_maps_pipeline_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(logs_route, "get_cache_client", lambda: None)

    def _raise_pipeline_error(db: MagicMock, query: str, top_k: int):
        raise IngestionPipelineError("similarity_query_failed")

    monkeypatch.setattr(logs_route, "find_similar_logs_by_query", _raise_pipeline_error)

    with pytest.raises(HTTPException) as exc:
        logs_route.search_similar_logs(query="test", top_k=3, db=MagicMock())

    assert exc.value.status_code == 500
    assert exc.value.detail == "Similarity search failed"


def test_search_similar_logs_uses_cache_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    cached = {
        "query": "amount mismatch",
        "total": 1,
        "results": [
            {
                "id": 42,
                "service_name": "checkout",
                "level": "ERROR",
                "message": "amount mismatch",
                "trace_id": "trace-c",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "similarity_score": 0.99,
            }
        ],
    }

    fake_cache = _FakeCache(seed={"any": cached})
    monkeypatch.setattr(logs_route, "build_cache_key", lambda *args, **kwargs: "any")
    monkeypatch.setattr(logs_route, "get_cache_client", lambda: fake_cache)
    monkeypatch.setattr(logs_route, "find_similar_logs_by_query", lambda *args, **kwargs: None)

    response = logs_route.search_similar_logs(query="amount mismatch", top_k=3, db=MagicMock())

    assert response.total == 1
    assert response.results[0].id == 42


def test_search_similar_logs_caches_on_first_call(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cache = _FakeCache()
    calls = {"count": 0}

    fake_log = SimpleNamespace(
        id=2,
        service_name="checkout",
        level="WARNING",
        message="amount mismatch",
        trace_id=None,
        timestamp=datetime.now(timezone.utc),
    )

    def _fake_find_similar_logs_by_query(db: MagicMock, query: str, top_k: int):
        calls["count"] += 1
        return [(fake_log, 0.91)]

    monkeypatch.setattr(logs_route, "build_cache_key", lambda *args, **kwargs: "same")
    monkeypatch.setattr(logs_route, "get_cache_client", lambda: fake_cache)
    monkeypatch.setattr(logs_route, "find_similar_logs_by_query", _fake_find_similar_logs_by_query)

    first = logs_route.search_similar_logs(query="amount mismatch", top_k=3, db=MagicMock())
    second = logs_route.search_similar_logs(query="amount mismatch", top_k=3, db=MagicMock())

    assert first.total == 1
    assert second.total == 1
    assert calls["count"] == 1
    assert fake_cache.set_calls == 1
