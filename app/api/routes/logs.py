import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.logs import (
    LogCreateRequest,
    LogCreateResponse,
    LogEmbeddingResponse,
    SimilarLogItem,
    SimilarLogsResponse,
)
from app.db.database import get_db
from app.services.ingestion_service import (
    create_log_entry,
    find_similar_logs,
    get_embedding_for_log,
)
from app.services.exceptions import IngestionPipelineError

router = APIRouter(tags=["logs"])
logger = logging.getLogger("app.routes.logs")


@router.post("/logs", response_model=LogCreateResponse, status_code=status.HTTP_201_CREATED)
def ingest_log(payload: LogCreateRequest, db: Session = Depends(get_db)) -> LogCreateResponse:
    try:
        log_entry = create_log_entry(db, payload)
    except IngestionPipelineError as exc:
        logger.exception(
            "ingestion_request_failed",
            extra={"service_name": payload.service_name, "trace_id": payload.trace_id},
        )
        raise HTTPException(status_code=500, detail="Log ingestion failed") from exc

    logger.info("ingestion_request_succeeded", extra={"log_id": log_entry.id})
    return LogCreateResponse(
        id=log_entry.id,
        service_name=log_entry.service_name,
        level=log_entry.level,
        message=log_entry.message,
        trace_id=log_entry.trace_id,
        timestamp=log_entry.timestamp,
    )


@router.get("/logs/{log_id}/embedding")
def get_log_embedding(
    log_id: int,
    include_vector: bool = False,
    db: Session = Depends(get_db),
) -> LogEmbeddingResponse:
    # reads embeddings directly from postgres (pgvector column).
    embedding = get_embedding_for_log(db=db, log_id=log_id)
    if embedding is None:
        logger.info("embedding_not_found", extra={"log_id": log_id})
        raise HTTPException(status_code=404, detail="Embedding not found for log")

    logger.info("embedding_fetch_succeeded", extra={"log_id": log_id})

    return LogEmbeddingResponse(
        log_id=log_id,
        embedding_dimension=len(embedding),
        embedding=embedding if include_vector else None,
    )


@router.get("/logs/similar", response_model=SimilarLogsResponse)
def search_similar_logs(
    query: str,
    top_k: int = 5,
    db: Session = Depends(get_db),
) -> SimilarLogsResponse:
    # this endpoint runs a vector similarity query in postgres and returns top-k nearest logs.
    safe_top_k = max(1, min(top_k, 20))
    try:
        similar = find_similar_logs(db=db, query=query, top_k=safe_top_k)
    except IngestionPipelineError as exc:
        logger.exception("similarity_request_failed", extra={"top_k": safe_top_k})
        raise HTTPException(status_code=500, detail="Similarity search failed") from exc

    results = [
        SimilarLogItem(
            id=log.id,
            service_name=log.service_name,
            level=log.level,
            message=log.message,
            trace_id=log.trace_id,
            timestamp=log.timestamp,
            similarity_score=score,
        )
        for log, score in similar
    ]

    logger.info("similarity_request_succeeded", extra={"result_count": len(results)})
    return SimilarLogsResponse(query=query, total=len(results), results=results)
