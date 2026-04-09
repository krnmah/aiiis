import logging
from functools import lru_cache

from app.core.config import get_settings
from app.llm.base_provider import BaseLLMProvider
from app.llm.huggingface_provider import HuggingFaceProvider
from app.llm.ollama_provider import OllamaProvider
from app.services.exceptions import LLMProviderError

logger = logging.getLogger("app.services.llm")


@lru_cache
def get_llm_provider() -> BaseLLMProvider:
    settings = get_settings()

    if settings.llm_provider == "ollama":
        return OllamaProvider()
    if settings.llm_provider == "huggingface":
        return HuggingFaceProvider()

    raise LLMProviderError(f"unsupported_llm_provider:{settings.llm_provider}")


def get_default_llm_model() -> str:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        return settings.ollama_model
    if settings.llm_provider == "huggingface":
        return settings.huggingface_model

    raise LLMProviderError(f"unsupported_llm_provider:{settings.llm_provider}")


def generate_with_local_llm(
    prompt: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> str:
    logger.info("llm_generation_started")
    text = get_llm_provider().generate(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
    )
    logger.info("llm_generation_succeeded")
    return text
