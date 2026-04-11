import logging
from functools import lru_cache

from app.core.config import get_settings
from app.llm.base_provider import BaseLLMProvider
from app.llm.huggingface_provider import HuggingFaceProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.ollama_provider import OllamaProvider
from app.services.exceptions import LLMProviderError

logger = logging.getLogger("app.services.llm")


@lru_cache
def get_llm_provider() -> BaseLLMProvider:
    settings = get_settings()
    return get_llm_provider_by_name(settings.llm_provider)


@lru_cache
def get_llm_provider_by_name(provider_name: str) -> BaseLLMProvider:
    if provider_name == "ollama":
        return OllamaProvider()
    if provider_name == "huggingface":
        return HuggingFaceProvider()
    if provider_name == "openai":
        return OpenAIProvider()

    raise LLMProviderError(f"unsupported_llm_provider:{provider_name}")


def get_default_llm_model() -> str:
    settings = get_settings()
    return get_default_llm_model_for_provider(settings.llm_provider)


def get_default_llm_model_for_provider(provider_name: str) -> str:
    settings = get_settings()
    if provider_name == "ollama":
        return settings.ollama_model
    if provider_name == "huggingface":
        return settings.huggingface_model
    if provider_name == "openai":
        return settings.openai_model

    raise LLMProviderError(f"unsupported_llm_provider:{provider_name}")


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


def generate_with_provider(
    provider_name: str,
    prompt: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> str:
    logger.info("llm_generation_started", extra={"provider": provider_name})
    text = get_llm_provider_by_name(provider_name).generate(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
    )
    logger.info("llm_generation_succeeded", extra={"provider": provider_name})
    return text
