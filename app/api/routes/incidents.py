import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.incidents import IncidentAnalyzeRequest, IncidentAnalyzeResponse
from app.db.database import get_db
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
    try:
        result = analyze_incident(db=db, query=payload.query, top_k=payload.top_k)
    except IncidentAnalysisError as exc:
        logger.exception("incident_analysis_request_failed")
        raise HTTPException(status_code=500, detail="Incident analysis failed") from exc

    logger.info(
        "incident_analysis_request_succeeded",
        extra={"analyzed_log_count": result.analyzed_log_count},
    )
    return IncidentAnalyzeResponse(
        query=result.query,
        root_cause=result.root_cause,
        analyzed_log_ids=result.analyzed_log_ids,
        analyzed_log_count=result.analyzed_log_count,
    )
