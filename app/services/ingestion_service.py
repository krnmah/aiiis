from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.logs import LogCreateRequest
from app.db.models import LogEntry
from app.embeddings.embedding_service import get_embedding_service


def create_log_entry(db: Session, payload: LogCreateRequest) -> LogEntry:
    # generates an embedding first so the same request creates both the raw log and its vector.
    embedding = get_embedding_service().embed_text(payload.message)

    log_entry = LogEntry(
        service_name=payload.service_name,
        level=payload.level,
        message=payload.message,
        trace_id=payload.trace_id,
        embedding=embedding,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )

    # persist the raw log and embedding record in PostgreSQL.
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return log_entry


def get_embedding_for_log(db: Session, log_id: int) -> list[float] | None:
    # fetches only the embedding column because that is all this endpoint needs.
    stmt = select(LogEntry.embedding).where(LogEntry.id == log_id)
    embedding = db.execute(stmt).scalar_one_or_none()
    return embedding


def find_similar_logs(db: Session, query: str, top_k: int) -> list[tuple[LogEntry, float]]:
    # convert the user query to a vector using the same model used at ingestion time.
    query_embedding = get_embedding_service().embed_text(query)

    distance_expr = LogEntry.embedding.cosine_distance(query_embedding)
    stmt = (
        select(LogEntry, distance_expr.label("distance"))
        .where(LogEntry.embedding.is_not(None))
        .order_by(distance_expr)
        .limit(top_k)
    )

    rows = db.execute(stmt).all()

    # cosine distance is better when smaller, so I mapped it to a score where higher is better.
    return [(row[0], float(1.0 - row[1])) for row in rows]
