from dataclasses import dataclass
import logging

from sqlalchemy.orm import Session

from app.services.exceptions import (
    IncidentAnalysisError,
    IngestionPipelineError,
    LLMProviderError,
)
from app.services.llm_service import generate_with_local_llm
from app.services.query_retrieval_service import find_similar_logs_by_query

logger = logging.getLogger("app.services.incident_analyzer")


SYSTEM_PROMPT = (
    "You are an SRE incident analyzer. Use only the provided logs and never invent missing facts. "
    "Return concise, actionable analysis with explicit evidence and confidence."
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
            "No related logs were retrieved. "
            "Return exactly:\n"
            "ROOT_CAUSE: insufficient evidence\n"
            "EVIDENCE: none\n"
            "CONFIDENCE: low\n"
            "NEXT_CHECKS: provide 2 concrete checks to collect missing evidence"
        )

    lines = []
    for log_entry, score in similar_logs:
        timestamp = getattr(log_entry, "timestamp", None)
        rendered_ts = timestamp.isoformat() if timestamp is not None else "unknown"
        lines.append(
            "- "
            f"log_id={log_entry.id}; "
            f"timestamp={rendered_ts}; "
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
        "Instructions:\n"
        "- infer the most likely single root cause\n"
        "- cite 2-4 strongest log facts as evidence\n"
        "- include confidence as high/medium/low\n"
        "- give 2 immediate validation checks\n\n"
        "Return in this exact format:\n"
        "ROOT_CAUSE: <one sentence>\n"
        "EVIDENCE:\n"
        "- <fact 1>\n"
        "- <fact 2>\n"
        "CONFIDENCE: <high|medium|low>\n"
        "NEXT_CHECKS:\n"
        "- <check 1>\n"
        "- <check 2>"
    )


def analyze_incident(db: Session, query: str, top_k: int = 5) -> IncidentAnalysisResult:
    logger.info("incident_analysis_started", extra={"top_k": top_k})

    safe_top_k = max(1, min(top_k, 20))
    try:
        similar_logs = find_similar_logs_by_query(db=db, query=query, top_k=safe_top_k)
    except IngestionPipelineError as exc:
        logger.exception("incident_log_retrieval_failed")
        raise IncidentAnalysisError("incident_log_retrieval_failed") from exc

    if not similar_logs:
        logger.info("incident_analysis_no_related_logs")
        return IncidentAnalysisResult(
            query=query,
            root_cause=(
                "ROOT_CAUSE: insufficient evidence from retrieved logs.\n"
                "EVIDENCE:\n"
                "- no related logs were found for this query\n"
                "CONFIDENCE: low\n"
                "NEXT_CHECKS:\n"
                "- verify the query terms and service scope\n"
                "- collect fresh error logs with matching trace identifiers"
            ),
            analyzed_log_ids=[],
            analyzed_log_count=0,
        )

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
