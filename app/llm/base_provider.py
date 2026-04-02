from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    # this is the minimal contract every llm provider must implement.
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        raise NotImplementedError
