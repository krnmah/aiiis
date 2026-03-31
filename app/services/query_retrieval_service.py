import logging

from sqlalchemy.orm import Session

from app.embeddings.embedding_service import get_embedding_service
from app.services.exceptions import IngestionPipelineError
from app.services.retrieval_service import find_similar_logs_by_embedding

logger = logging.getLogger("app.query_retrieval")


def find_similar_logs_by_query(db: Session, query: str, top_k: int):
    # text query -> embedding -> top-k similar logs.
    try:
        query_embedding = get_embedding_service().embed_text(query)
    except Exception as exc:
        logger.exception("query_embedding_generation_failed")
        raise IngestionPipelineError("query_embedding_generation_failed") from exc

    return find_similar_logs_by_embedding(
        db=db,
        query_embedding=query_embedding,
        top_k=top_k,
    )
