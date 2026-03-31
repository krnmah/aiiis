from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import query_retrieval_service
from app.services.exceptions import IngestionPipelineError


class _FakeEmbeddingService:
    # keep this fake tiny so tests stay fast and don't initialize heavy models.
    def __init__(self, embedding: list[float]) -> None:
        self._embedding = embedding

    def embed_text(self, _: str) -> list[float]:
        return self._embedding


def test_find_similar_logs_by_query_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        query_retrieval_service,
        "get_embedding_service",
        lambda: _FakeEmbeddingService([0.01, 0.02]),
    )

    fake_log = SimpleNamespace(
        id=1,
        service_name="checkout",
        level="ERROR",
        message="amount mismatch",
        trace_id="trace-x",
        timestamp=datetime.now(timezone.utc),
    )

    captured: dict[str, object] = {}

    def _fake_find_by_embedding(db: MagicMock, query_embedding: list[float], top_k: int):
        captured["query_embedding"] = query_embedding
        captured["top_k"] = top_k
        return [(fake_log, 0.77)]

    monkeypatch.setattr(
        query_retrieval_service,
        "find_similar_logs_by_embedding",
        _fake_find_by_embedding,
    )

    result = query_retrieval_service.find_similar_logs_by_query(
        db=MagicMock(),
        query="amount mismatch",
        top_k=4,
    )

    assert captured["query_embedding"] == [0.01, 0.02]
    assert captured["top_k"] == 4
    assert result[0][0].id == 1
    assert result[0][1] == 0.77


def test_find_similar_logs_by_query_embedding_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BrokenEmbeddingService:
        def embed_text(self, _: str) -> list[float]:
            raise RuntimeError("model unavailable")

    monkeypatch.setattr(
        query_retrieval_service,
        "get_embedding_service",
        lambda: _BrokenEmbeddingService(),
    )

    with pytest.raises(IngestionPipelineError, match="query_embedding_generation_failed"):
        query_retrieval_service.find_similar_logs_by_query(
            db=MagicMock(),
            query="amount mismatch",
            top_k=4,
        )
