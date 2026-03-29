import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import LogEntry
from app.embeddings.embedding_service import get_embedding_service
from app.services.exceptions import IngestionPipelineError

logger = logging.getLogger("app.retrieval")


def get_embedding_for_log(db: Session, log_id: int) -> list[float] | None:
    # keep this read lightweight by selecting only the embedding column.
    stmt = select(LogEntry.embedding).where(LogEntry.id == log_id)
    embedding = db.execute(stmt).scalar_one_or_none()
    return embedding


def find_similar_logs(db: Session, query: str, top_k: int) -> list[tuple[LogEntry, float]]:
    logger.info("similarity_search_started", extra={"top_k": top_k})

    try:
        # use the same embedding model as ingestion so vectors are comparable in one space.
        query_embedding = get_embedding_service().embed_text(query)
    except Exception as exc:
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

    # cosine distance is lower for better matches, so convert to higher-is-better score.
    results = [(row[0], float(1.0 - row[1])) for row in rows]
    logger.info("similarity_search_succeeded", extra={"result_count": len(results)})
    return results
