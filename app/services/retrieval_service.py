import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, defer

from app.db.models import LogEntry
from app.services.exceptions import IngestionPipelineError

logger = logging.getLogger("app.retrieval")


def get_log_by_id(db: Session, log_id: int) -> LogEntry | None:
    # fetch only the requested row, keeping this endpoint straightforward and fast.
    stmt = select(LogEntry).where(LogEntry.id == log_id)
    return db.execute(stmt).scalar_one_or_none()


def get_embedding_for_log(db: Session, log_id: int) -> list[float] | None:
    # keep this read lightweight by selecting only the embedding column.
    stmt = select(LogEntry.embedding).where(LogEntry.id == log_id)
    embedding = db.execute(stmt).scalar_one_or_none()
    return embedding


def find_similar_logs_by_embedding(
    db: Session,
    query_embedding: list[float],
    top_k: int,
) -> list[tuple[LogEntry, float]]:
    # this module handles vector search in db, not text query embedding.
    logger.info("similarity_search_started", extra={"top_k": top_k})

    distance_expr = LogEntry.embedding.cosine_distance(query_embedding)
    stmt = (
        select(LogEntry, distance_expr.label("distance"))
        .options(defer(LogEntry.embedding))
        .where(LogEntry.embedding.is_not(None))
        .order_by(distance_expr)
        .limit(top_k)
    )

    try:
        rows = db.execute(stmt).all()
    except SQLAlchemyError as exc:
        logger.exception("similarity_query_failed")
        raise IngestionPipelineError("similarity_query_failed") from exc

    # cosine distance is lower for better matches.
    # convert it to a higher-is-better similarity score.
    results = [(row[0], float(1.0 - row[1])) for row in rows]
    logger.info(
        "similarity_search_succeeded",
        extra={"result_count": len(results)},
    )
    return results
