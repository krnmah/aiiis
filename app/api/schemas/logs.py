from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LogCreateRequest(BaseModel):
    service_name: str = Field(min_length=1, max_length=120)
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str = Field(min_length=1, max_length=5000)
    trace_id: str | None = Field(default=None, max_length=120)
    timestamp: datetime | None = None


class LogCreateResponse(BaseModel):
    id: int
    service_name: str
    level: str
    message: str
    trace_id: str | None
    timestamp: datetime


class LogEmbeddingResponse(BaseModel):
    log_id: int
    embedding_dimension: int
    embedding: list[float] | None = None


class SimilarLogItem(BaseModel):
    id: int
    service_name: str
    level: str
    message: str
    trace_id: str | None
    timestamp: datetime
    similarity_score: float


class SimilarLogsResponse(BaseModel):
    query: str
    total: int
    results: list[SimilarLogItem]
