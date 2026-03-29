from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.api.schemas.logs import LogCreateRequest
from app.services.exceptions import IngestionPipelineError
from app.services import ingestion_service


class _FakeEmbeddingService:
    # keep this tiny fake so tests don't load the real sentence-transformers model.
    def __init__(self, embedding: list[float]) -> None:
        self._embedding = embedding

    def embed_text(self, _: str) -> list[float]:
        return self._embedding


def test_create_log_entry_success(monkeypatch: pytest.MonkeyPatch) -> None:
    # use fake embeddings so this test stays fast and deterministic.
    monkeypatch.setattr(
        ingestion_service,
        "get_embedding_service",
        lambda: _FakeEmbeddingService([0.1, 0.2, 0.3]),
    )

    db = MagicMock()

    def _refresh_side_effect(log_obj: object) -> None:
        setattr(log_obj, "id", 101)

    db.refresh.side_effect = _refresh_side_effect

    payload = LogCreateRequest(
        service_name="billing-service",
        level="ERROR",
        message="invoice mismatch",
        trace_id="trace-1",
        timestamp=datetime.now(timezone.utc),
    )

    result = ingestion_service.create_log_entry(db=db, payload=payload)

    assert result.id == 101
    assert result.embedding == [0.1, 0.2, 0.3]
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_create_log_entry_rolls_back_on_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ingestion_service,
        "get_embedding_service",
        lambda: _FakeEmbeddingService([0.9, 0.8]),
    )

    db = MagicMock()
    db.commit.side_effect = SQLAlchemyError("insert failed")

    payload = LogCreateRequest(
        service_name="auth-service",
        level="ERROR",
        message="db issue",
        trace_id="trace-2",
    )

    with pytest.raises(IngestionPipelineError, match="ingestion_db_write_failed"):
        ingestion_service.create_log_entry(db=db, payload=payload)

    db.rollback.assert_called_once()
