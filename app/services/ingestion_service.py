from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.api.schemas.logs import LogCreateRequest
from app.db.models import LogEntry


def create_log_entry(db: Session, payload: LogCreateRequest) -> LogEntry:
    log_entry = LogEntry(
        service_name=payload.service_name,
        level=payload.level,
        message=payload.message,
        trace_id=payload.trace_id,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
