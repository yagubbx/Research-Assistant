"""Killable synchronous synthesis worker; stdout is a JSON-only protocol."""

import asyncio
import json
import os
import sys
from typing import Literal

import httpx
from pydantic import BaseModel

import ai
from ai.providers.base import LLMProvider, ProviderError
from ai.providers.factory import get_llm
from ai.schemas import Source
from researcher.config import Settings
from researcher.offline import OfflineLLM
from researcher.resilience import RetryTransport


class ResearchLLM(LLMProvider):
    """Allow enough output budget for reasoning models and a complete answer."""

    def __init__(self) -> None:
        self.provider = get_llm()

    def complete(self, prompt: str, *, json_schema: dict | None = None, max_tokens: int = 1024) -> str:
        return self.provider.complete(prompt, json_schema=json_schema, max_tokens=max(4096, max_tokens))


class SynthesisRequest(BaseModel):
    """Typed subprocess input; contains evidence but no API keys."""

    question: str
    sources: list[Source]
    offline: bool = False
    operation: Literal["synthesize", "web"] = "synthesize"
    max_results: int = 3
    web_provider: Literal["tavily", "serper", "duckduckgo"] | None = None


class SourceBatch(BaseModel):
    """Typed response for an isolated keyless search call."""

    sources: list[Source]


async def fetch_web(request: SynthesisRequest) -> list[Source]:
    """Apply the same HTTP retry policy inside the isolated web process."""
    settings = Settings.from_env()
    async with httpx.AsyncClient(transport=RetryTransport(settings), timeout=settings.http_timeout) as client:
        return await ai.fetch_web(request.question, max_results=request.max_results, client=client)


def main() -> int:
    """Run the provided function and redact provider exception messages."""
    try:
        request = SynthesisRequest.model_validate_json(sys.stdin.read())
        if request.operation == "web":
            if request.web_provider:
                os.environ["WEB_SEARCH_PROVIDER"] = request.web_provider
            sources = asyncio.run(fetch_web(request))
            sys.stdout.write(SourceBatch(sources=sources).model_dump_json())
            return 0
        result = ai.synthesize(
            request.question, request.sources, llm=OfflineLLM() if request.offline else ResearchLLM()
        )
        sys.stdout.write(result.model_dump_json())
        return 0
    except (ProviderError, ValueError, OSError, TypeError, AttributeError, KeyError) as error:
        cause: BaseException | None = error
        status = None
        while cause:
            status = getattr(cause, "status_code", status)
            cause = cause.__cause__
        sys.stdout.write(json.dumps({"error": type(error).__name__, "status": status}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
