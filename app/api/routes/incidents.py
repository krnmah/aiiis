import logging
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.incidents import IncidentAnalyzeRequest, IncidentAnalyzeResponse
from app.cache.redis_cache import build_cache_key, get_cache_client
from app.core.config import get_settings
from app.db.database import get_db
from app.metrics.prometheus_metrics import observe_request
from app.services.exceptions import IncidentAnalysisError
from app.services.incident_analyzer_service import analyze_incident

router = APIRouter(tags=["incidents"])
logger = logging.getLogger("app.routes.incidents")


@router.post(
    "/incidents",
    response_model=IncidentAnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_incident_route(
    payload: IncidentAnalyzeRequest,
    db: Session = Depends(get_db),
) -> IncidentAnalyzeResponse:
    start_time = perf_counter()
    status_code = 200
    settings = get_settings()
    cache_key = build_cache_key(
        "incident_analysis",
        query=payload.query,
        top_k=payload.top_k,
    )
    cache = get_cache_client()

    if cache is not None:
        cached_payload = cache.get_json(cache_key)
        if cached_payload is not None:
            logger.info("incident_analysis_cache_hit", extra={"top_k": payload.top_k})
            return IncidentAnalyzeResponse(**cached_payload)

    try:
        result = analyze_incident(db=db, query=payload.query, top_k=payload.top_k)
    except IncidentAnalysisError as exc:
        status_code = 500
        logger.exception("incident_analysis_request_failed")
        raise HTTPException(status_code=500, detail="Incident analysis failed") from exc
    finally:
        observe_request(
            endpoint="/incidents",
            method="POST",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )

    logger.info(
        "incident_analysis_request_succeeded",
        extra={"analyzed_log_count": result.analyzed_log_count},
    )
    response = IncidentAnalyzeResponse(
        query=result.query,
        root_cause=result.root_cause,
        analyzed_log_ids=result.analyzed_log_ids,
        analyzed_log_count=result.analyzed_log_count,
    )

    if cache is not None:
        cache.set_json(
            key=cache_key,
            payload=response.model_dump(mode="json"),
            ttl_seconds=settings.redis_cache_ttl_seconds,
        )

    return response
