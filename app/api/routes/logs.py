import logging
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.logs import (
    LogCreateRequest,
    LogCreateResponse,
    LogDetailResponse,
    LogEmbeddingResponse,
    SimilarLogItem,
    SimilarLogsResponse,
)
from app.cache.redis_cache import build_cache_key, get_cache_client
from app.core.config import get_settings
from app.db.database import get_db
from app.metrics.prometheus_metrics import observe_request
from app.services.ingestion_service import create_log_entry
from app.services.query_retrieval_service import find_similar_logs_by_query
from app.services.retrieval_service import get_embedding_for_log, get_log_by_id
from app.services.exceptions import IngestionPipelineError

router = APIRouter(tags=["logs"])
logger = logging.getLogger("app.routes.logs")


@router.post(
    "/logs",
    response_model=LogCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_log(
    payload: LogCreateRequest,
    db: Session = Depends(get_db),
) -> LogCreateResponse:
    start_time = perf_counter()
    status_code = 201
    try:
        log_entry = create_log_entry(db, payload)
    except IngestionPipelineError as exc:
        status_code = 500
        logger.exception(
            "ingestion_request_failed",
            extra={
                "service_name": payload.service_name,
                "trace_id": payload.trace_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Log ingestion failed",
        ) from exc
    finally:
        observe_request(
            endpoint="/logs",
            method="POST",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )

    logger.info(
        "ingestion_request_succeeded",
        extra={"log_id": log_entry.id},
    )
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
    start_time = perf_counter()
    status_code = 200
    try:
        # reads embeddings directly from postgres (pgvector column).
        embedding = get_embedding_for_log(db=db, log_id=log_id)
        if embedding is None:
            status_code = 404
            logger.info("embedding_not_found", extra={"log_id": log_id})
            raise HTTPException(
                status_code=404,
                detail="Embedding not found for log",
            )

        logger.info("embedding_fetch_succeeded", extra={"log_id": log_id})

        return LogEmbeddingResponse(
            log_id=log_id,
            embedding_dimension=len(embedding),
            embedding=embedding if include_vector else None,
        )
    finally:
        observe_request(
            endpoint="/logs/{log_id}/embedding",
            method="GET",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )


@router.get("/logs/similar", response_model=SimilarLogsResponse)
def search_similar_logs(
    query: str,
    top_k: int = 5,
    db: Session = Depends(get_db),
) -> SimilarLogsResponse:
    start_time = perf_counter()
    status_code = 200
    settings = get_settings()
    # this endpoint runs vector similarity in postgres.
    # it returns the top-k nearest logs.
    safe_top_k = max(1, min(top_k, 20))
    cache_key = build_cache_key(
        "similar_logs",
        query=query,
        top_k=safe_top_k,
    )
    cache = get_cache_client()

    if cache is not None:
        cached_payload = cache.get_json(cache_key)
        if cached_payload is not None:
            logger.info("similarity_cache_hit", extra={"top_k": safe_top_k})
            return SimilarLogsResponse(**cached_payload)

    try:
        similar = find_similar_logs_by_query(
            db=db,
            query=query,
            top_k=safe_top_k,
        )
    except IngestionPipelineError as exc:
        status_code = 500
        logger.exception(
            "similarity_request_failed",
            extra={"top_k": safe_top_k},
        )
        raise HTTPException(
            status_code=500,
            detail="Similarity search failed",
        ) from exc
    finally:
        observe_request(
            endpoint="/logs/similar",
            method="GET",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )

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

    logger.info(
        "similarity_request_succeeded",
        extra={"result_count": len(results)},
    )
    response = SimilarLogsResponse(
        query=query,
        total=len(results),
        results=results,
    )

    if cache is not None:
        cache.set_json(
            key=cache_key,
            payload=response.model_dump(mode="json"),
            ttl_seconds=(settings.redis_cache_ttl_seconds),
        )

    return response


@router.get("/logs/{log_id}", response_model=LogDetailResponse)
def get_log_detail(log_id: int, db: Session = Depends(get_db)) -> LogDetailResponse:
    start_time = perf_counter()
    status_code = 200
    try:
        log_entry = get_log_by_id(db=db, log_id=log_id)
        if log_entry is None:
            status_code = 404
            logger.info("log_detail_not_found", extra={"log_id": log_id})
            raise HTTPException(status_code=404, detail="Log not found")

        logger.info("log_detail_fetch_succeeded", extra={"log_id": log_id})
        return LogDetailResponse(
            id=log_entry.id,
            service_name=log_entry.service_name,
            level=log_entry.level,
            message=log_entry.message,
            trace_id=log_entry.trace_id,
            timestamp=log_entry.timestamp,
        )
    finally:
        observe_request(
            endpoint="/logs/{log_id}",
            method="GET",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )
