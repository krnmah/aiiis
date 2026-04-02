from pydantic import BaseModel, Field


class LLMGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    system_prompt: str | None = Field(default=None, max_length=8000)
    model: str | None = Field(default=None, max_length=200)


class LLMGenerateResponse(BaseModel):
    provider: str
    model: str
    response: str
