from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.logs import LogCreateRequest, LogCreateResponse
from app.db.database import get_db
from app.services.ingestion_service import create_log_entry
from app.vector_store.in_memory_store import get_embedding_store

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
def get_log_embedding(log_id: int, include_vector: bool = False) -> dict:
    # read the temporary embedding generated at ingestion time.
    embedding = get_embedding_store().get(log_id=log_id)
    if embedding is None:
        raise HTTPException(status_code=404, detail="Embedding not found for log")

    response: dict[str, object] = {
        "log_id": log_id,
        "embedding_dimension": len(embedding),
    }

    # keep full vector output optional to avoid large default responses.
    if include_vector:
        response["embedding"] = embedding

    return response
