import logging
from time import perf_counter

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.llm import LLMGenerateRequest, LLMGenerateResponse
from app.core.config import get_settings
from app.metrics.prometheus_metrics import observe_request
from app.services.exceptions import LLMProviderError
from app.services.llm_service import generate_with_local_llm

router = APIRouter(tags=["llm"])
logger = logging.getLogger("app.routes.llm")


@router.post("/llm/test", response_model=LLMGenerateResponse, status_code=status.HTTP_200_OK)
def test_local_llm(payload: LLMGenerateRequest) -> LLMGenerateResponse:
    start_time = perf_counter()
    status_code = 200
    settings = get_settings()
    selected_model = payload.model or settings.ollama_model

    try:
        response_text = generate_with_local_llm(
            prompt=payload.prompt,
            system_prompt=payload.system_prompt,
            model=payload.model,
        )
    except LLMProviderError as exc:
        status_code = 503
        logger.exception("llm_test_failed", extra={"model": selected_model})
        raise HTTPException(status_code=503, detail="Local LLM request failed") from exc
    finally:
        observe_request(
            endpoint="/llm/test",
            method="POST",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )

    logger.info("llm_test_succeeded", extra={"model": selected_model})
    return LLMGenerateResponse(
        provider=settings.llm_provider,
        model=selected_model,
        response=response_text,
    )
