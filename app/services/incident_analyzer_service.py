from dataclasses import dataclass
import logging

from sqlalchemy.orm import Session

from app.services.exceptions import IncidentAnalysisError, IngestionPipelineError, LLMProviderError
from app.services.llm_service import generate_with_local_llm
from app.services.query_retrieval_service import find_similar_logs_by_query

logger = logging.getLogger("app.services.incident_analyzer")


SYSTEM_PROMPT = (
    "You are an SRE incident analyzer. Use only the provided logs to infer the most likely root cause. "
    "If evidence is weak, state uncertainty clearly and suggest the next concrete validation step."
)


@dataclass
class IncidentAnalysisResult:
    query: str
    root_cause: str
    analyzed_log_ids: list[int]
    analyzed_log_count: int


def _build_incident_prompt(query: str, similar_logs: list[tuple[object, float]]) -> str:
    if not similar_logs:
        return (
            "Incident query:\n"
            f"{query}\n\n"
            "Related logs:\n"
            "- no related logs found\n\n"
            "Return a short root cause analysis and immediate next check."
        )

    lines = []
    for log_entry, score in similar_logs:
        lines.append(
            "- "
            f"log_id={log_entry.id}; "
            f"service={log_entry.service_name}; "
            f"level={log_entry.level}; "
            f"trace_id={log_entry.trace_id or 'none'}; "
            f"similarity={score:.3f}; "
            f"message={log_entry.message}"
        )

    joined_logs = "\n".join(lines)
    return (
        "Incident query:\n"
        f"{query}\n\n"
        "Related logs:\n"
        f"{joined_logs}\n\n"
        "Return a short root cause analysis and immediate next check."
    )


def analyze_incident(db: Session, query: str, top_k: int = 5) -> IncidentAnalysisResult:
    logger.info("incident_analysis_started", extra={"top_k": top_k})

    safe_top_k = max(1, min(top_k, 20))
    try:
        similar_logs = find_similar_logs_by_query(db=db, query=query, top_k=safe_top_k)
    except IngestionPipelineError as exc:
        logger.exception("incident_log_retrieval_failed")
        raise IncidentAnalysisError("incident_log_retrieval_failed") from exc

    prompt = _build_incident_prompt(query=query, similar_logs=similar_logs)

    try:
        root_cause = generate_with_local_llm(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
        )
    except LLMProviderError as exc:
        logger.exception("incident_analysis_llm_failed")
        raise IncidentAnalysisError("incident_analysis_llm_failed") from exc

    clean_root_cause = root_cause.strip()
    if not clean_root_cause:
        logger.error("incident_analysis_empty_response")
        raise IncidentAnalysisError("incident_analysis_empty_response")

    analyzed_ids = [log_entry.id for log_entry, _ in similar_logs]

    logger.info(
        "incident_analysis_succeeded",
        extra={"analyzed_log_count": len(analyzed_ids)},
    )
    return IncidentAnalysisResult(
        query=query,
        root_cause=clean_root_cause,
        analyzed_log_ids=analyzed_ids,
        analyzed_log_count=len(analyzed_ids),
    )
