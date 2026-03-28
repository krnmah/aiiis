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

router = APIRouter(tags=["logs"])


@router.post("/logs", response_model=LogCreateResponse, status_code=status.HTTP_201_CREATED)
def ingest_log(payload: LogCreateRequest, db: Session = Depends(get_db)) -> LogCreateResponse:
    log_entry = create_log_entry(db, payload)
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
        raise HTTPException(status_code=404, detail="Embedding not found for log")

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
    similar = find_similar_logs(db=db, query=query, top_k=safe_top_k)

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

    return SimilarLogsResponse(query=query, total=len(results), results=results)
