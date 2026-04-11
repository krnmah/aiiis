import logging
from time import perf_counter

from fastapi import APIRouter, HTTPException, Query, status

from app.api.schemas.llm import (
    LLMCompareRequest,
    LLMCompareResponse,
    LLMCompareResult,
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMModelCheckResponse,
)
from app.core.config import get_settings
from app.metrics.prometheus_metrics import observe_request
from app.services.exceptions import LLMProviderError
from app.services.llm_service import (
    generate_with_local_llm,
    generate_with_provider,
    get_default_llm_model,
    get_default_llm_model_for_provider,
)

router = APIRouter(tags=["llm"])
logger = logging.getLogger("app.routes.llm")


@router.post(
    "/llm/test", response_model=LLMGenerateResponse, status_code=status.HTTP_200_OK
)
def test_local_llm(payload: LLMGenerateRequest) -> LLMGenerateResponse:
    start_time = perf_counter()
    status_code = 200
    settings = get_settings()
    selected_model = payload.model or get_default_llm_model()

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


@router.get(
    "/llm/model/check",
    response_model=LLMModelCheckResponse,
    status_code=status.HTTP_200_OK,
)
def check_llm_model(
    model: str | None = Query(default=None, max_length=200)
) -> LLMModelCheckResponse:
    start_time = perf_counter()
    status_code = 200
    settings = get_settings()
    selected_model = model or get_default_llm_model()

    try:
        generate_with_local_llm(prompt="healthcheck", model=selected_model)
        detail = "model_available"
        available = True
    except LLMProviderError as exc:
        status_code = 503
        logger.warning("llm_model_check_failed", extra={"model": selected_model})
        detail = str(exc)
        available = False
    finally:
        observe_request(
            endpoint="/llm/model/check",
            method="GET",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )

    return LLMModelCheckResponse(
        provider=settings.llm_provider,
        model=selected_model,
        available=available,
        detail=detail,
    )


@router.post(
    "/llm/compare", response_model=LLMCompareResponse, status_code=status.HTTP_200_OK
)
def compare_llm_outputs(payload: LLMCompareRequest) -> LLMCompareResponse:
    start_time = perf_counter()
    status_code = 200
    results: list[LLMCompareResult] = []

    try:
        for provider_name in payload.providers:
            model = payload.model_overrides.get(
                provider_name
            ) or get_default_llm_model_for_provider(provider_name)
            try:
                text = generate_with_provider(
                    provider_name=provider_name,
                    prompt=payload.prompt,
                    system_prompt=payload.system_prompt,
                    model=model,
                )
                results.append(
                    LLMCompareResult(
                        provider=provider_name,
                        model=model,
                        response=text,
                    )
                )
            except LLMProviderError as exc:
                status_code = 207
                logger.warning(
                    "llm_compare_provider_failed",
                    extra={"provider": provider_name, "model": model},
                )
                results.append(
                    LLMCompareResult(
                        provider=provider_name,
                        model=model,
                        error=str(exc),
                    )
                )
    finally:
        observe_request(
            endpoint="/llm/compare",
            method="POST",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )

    return LLMCompareResponse(results=results)
