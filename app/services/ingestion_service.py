from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.api.schemas.logs import LogCreateRequest
from app.db.models import LogEntry
from app.embeddings.embedding_service import get_embedding_service
from app.vector_store.in_memory_store import get_embedding_store


def create_log_entry(db: Session, payload: LogCreateRequest) -> LogEntry:
    # generates an embedding first so the same request creates both the raw log and its vector.
    embedding = get_embedding_service().embed_text(payload.message)

    log_entry = LogEntry(
        service_name=payload.service_name,
        level=payload.level,
        message=payload.message,
        trace_id=payload.trace_id,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )

    # persist the raw log record in PostgreSQL.
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    # temporarily store the embedding in-memory until pgvector integration is implemented.
    get_embedding_store().upsert(log_id=log_entry.id, embedding=embedding)

    return log_entry
