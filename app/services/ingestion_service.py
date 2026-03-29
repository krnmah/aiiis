from datetime import datetime, timezone
import logging

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
