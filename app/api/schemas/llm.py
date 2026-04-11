from pydantic import BaseModel, Field


class LLMGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    system_prompt: str | None = Field(default=None, max_length=8000)
    model: str | None = Field(default=None, max_length=200)


class LLMGenerateResponse(BaseModel):
    provider: str
    model: str
    response: str


class LLMModelCheckResponse(BaseModel):
    provider: str
    model: str
    available: bool
    detail: str


class LLMCompareRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    system_prompt: str | None = Field(default=None, max_length=8000)
    providers: list[str] = Field(default_factory=lambda: ["huggingface", "openai"], min_length=1)
    model_overrides: dict[str, str] = Field(default_factory=dict)


class LLMCompareResult(BaseModel):
    provider: str
    model: str
    response: str | None = None
    error: str | None = None


class LLMCompareResponse(BaseModel):
    results: list[LLMCompareResult]
