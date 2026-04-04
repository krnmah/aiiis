from pydantic import BaseModel, Field


class IncidentAnalyzeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=20)


class IncidentAnalyzeResponse(BaseModel):
    query: str
    root_cause: str
    analyzed_log_ids: list[int]
    analyzed_log_count: int
