from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas.logs import LogCreateRequest, LogCreateResponse
from app.db.database import get_db
from app.services.ingestion_service import create_log_entry

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
