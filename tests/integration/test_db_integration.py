from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.db.database import SessionLocal, check_db_connection, initialize_database
from app.db.models import LogEntry


def _require_db() -> None:
    try:
        check_db_connection()
    except Exception as exc:
        pytest.skip(f"PostgreSQL not reachable for integration test: {exc}")


def test_db_connection_works() -> None:
    _require_db()
    assert check_db_connection() is True


def test_logs_table_round_trip() -> None:
    _require_db()
    initialize_database()

    unique_trace_id = f"it-db-{uuid4().hex[:12]}"

    session = SessionLocal()
    try:
        entry = LogEntry(
            service_name="integration-db",
            level="INFO",
            message="integration db write/read test",
            trace_id=unique_trace_id,
            embedding=None,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(entry)
        session.commit()

        loaded = (
            session.query(LogEntry)
            .filter(LogEntry.trace_id == unique_trace_id)
            .order_by(LogEntry.id.desc())
            .first()
        )

        assert loaded is not None
        assert loaded.service_name == "integration-db"
        assert loaded.message == "integration db write/read test"
    finally:
        session.query(LogEntry).filter(LogEntry.trace_id == unique_trace_id).delete()
        session.commit()
        session.close()
