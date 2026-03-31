from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.services import retrieval_service
from app.services.exceptions import IngestionPipelineError


def test_get_embedding_for_log_returns_vector() -> None:
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = [0.11, 0.22]

    result = retrieval_service.get_embedding_for_log(db=db, log_id=7)

    assert result == [0.11, 0.22]


def test_find_similar_logs_by_embedding_returns_scores() -> None:
    db = MagicMock()
    fake_log = SimpleNamespace(
        id=1,
        service_name="checkout",
        level="ERROR",
        message="amount mismatch",
        trace_id="trace-x",
        timestamp=datetime.now(timezone.utc),
    )
    # db returns cosine distance=0.2, so score should become 0.8.
    db.execute.return_value.all.return_value = [(fake_log, 0.2)]

    results = retrieval_service.find_similar_logs_by_embedding(
        db=db,
        query_embedding=[0.01, 0.02],
        top_k=3,
    )

    assert len(results) == 1
    assert results[0][0].id == 1
    assert pytest.approx(results[0][1], rel=1e-6) == 0.8


def test_find_similar_logs_by_embedding_db_failure() -> None:
    db = MagicMock()
    db.execute.side_effect = SQLAlchemyError("query failed")

    with pytest.raises(IngestionPipelineError, match="similarity_query_failed"):
        retrieval_service.find_similar_logs_by_embedding(
            db=db,
            query_embedding=[0.01, 0.02],
            top_k=2,
        )
