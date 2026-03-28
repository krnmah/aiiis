from datetime import datetime, timezone
import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.schemas.logs import LogCreateRequest
from app.db.models import LogEntry
from app.embeddings.embedding_service import get_embedding_service
from app.services.exceptions import IngestionPipelineError

logger = logging.getLogger("app.ingestion")


def create_log_entry(db: Session, payload: LogCreateRequest) -> LogEntry:
    # this keeps a clear trace when ingestion starts for a given service/log level.
    logger.info(
        "ingestion_started",
        extra={
            "service_name": payload.service_name,
            "log_level": payload.level,
            "trace_id": payload.trace_id,
        },
    )

    try:
        # first step: generate embedding so raw text and vector stay in sync.
        embedding = get_embedding_service().embed_text(payload.message)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "embedding_generation_failed",
            extra={"service_name": payload.service_name, "trace_id": payload.trace_id},
        )
        raise IngestionPipelineError("embedding_generation_failed") from exc

    log_entry = LogEntry(
        service_name=payload.service_name,
        level=payload.level,
        message=payload.message,
        trace_id=payload.trace_id,
        embedding=embedding,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )

    try:
        # second step: persist raw log + embedding in a single db transaction.
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(
            "ingestion_db_write_failed",
            extra={"service_name": payload.service_name, "trace_id": payload.trace_id},
        )
        raise IngestionPipelineError("ingestion_db_write_failed") from exc

    logger.info(
        "ingestion_succeeded",
        extra={
            "log_id": log_entry.id,
            "service_name": log_entry.service_name,
            "trace_id": log_entry.trace_id,
        },
    )

    return log_entry


def get_embedding_for_log(db: Session, log_id: int) -> list[float] | None:
    # this fetches only the vector column so the read stays light.
    stmt = select(LogEntry.embedding).where(LogEntry.id == log_id)
    embedding = db.execute(stmt).scalar_one_or_none()
    return embedding


def find_similar_logs(db: Session, query: str, top_k: int) -> list[tuple[LogEntry, float]]:
    logger.info("similarity_search_started", extra={"top_k": top_k})

    try:
        # this uses the same embedding model as ingestion to keep vector space consistent.
        query_embedding = get_embedding_service().embed_text(query)
    except Exception as exc:  # noqa: BLE001
        logger.exception("similarity_embedding_generation_failed")
        raise IngestionPipelineError("similarity_embedding_generation_failed") from exc

    distance_expr = LogEntry.embedding.cosine_distance(query_embedding)
    stmt = (
        select(LogEntry, distance_expr.label("distance"))
        .where(LogEntry.embedding.is_not(None))
        .order_by(distance_expr)
        .limit(top_k)
    )

    try:
        rows = db.execute(stmt).all()
    except SQLAlchemyError as exc:
        logger.exception("similarity_query_failed")
        raise IngestionPipelineError("similarity_query_failed") from exc

    # cosine distance is lower for better matches, so I convert it to higher-is-better score.
    results = [(row[0], float(1.0 - row[1])) for row in rows]
    logger.info("similarity_search_succeeded", extra={"result_count": len(results)})
    return results
