"""The only application boundary that calls the provided AI package."""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Literal, cast

import httpx

import ai
from ai.providers.base import ProviderError
from ai.schemas import AnswerWithCitations, Source
from researcher.bonuses import FailoverProvider, TokenBudget
from researcher.config import Settings
from researcher.logging_config import debug_payload, info_payload
from researcher.offline import OfflineWeb
from researcher.resilience import RateLimiter, retry
from researcher.validation import validate_answer
from researcher.worker import SourceBatch, SynthesisRequest

log = logging.getLogger(__name__)


class AIService:
    """Compose retries, hard process deadlines and the immutable AI module."""

    def __init__(self, settings: Settings, offline: bool = False) -> None:
        self.settings, self.offline = settings, offline
        self.web_limiter = RateLimiter(settings.rate_interval, settings.arxiv_interval)
        self.token_budget = TokenBudget(getattr(settings, f"{settings.llm_provider}_tpm"))

    async def fetch(self, name: str, query: str, client: httpx.AsyncClient) -> list[Source]:
        """Retry an AI fetch while the orchestrator enforces its total deadline."""
        info_payload(log, "fetch_input", f"{name}: {query}")

        @retry(self.settings)
        async def call() -> list[Source]:
            if name == "wiki":
                return await ai.fetch_wikipedia(query, client=client, max_results=self.settings.max_results)
            if name == "arxiv":
                return await ai.fetch_arxiv(query, client=client, max_results=self.settings.max_results)
            if name == "web":
                if not self.offline and self.settings.web_search_provider == "duckduckgo":
                    await self.web_limiter.acquire("duckduckgo.com")
                    request = SynthesisRequest(
                        question=query, sources=[], operation="web", max_results=self.settings.max_results
                    )
                    return SourceBatch.model_validate_json(await self._worker(request)).sources
                return await ai.fetch_web(
                    query,
                    client=client,
                    max_results=self.settings.max_results,
                    provider=OfflineWeb() if self.offline else None,
                )
            raise ValueError("Unknown source")

        try:
            if name == "web" and not self.offline and self.settings.web_fallbacks:
                providers = [self.settings.web_search_provider, *self.settings.web_fallbacks.split(",")]
                sources = await FailoverProvider(providers, self.settings.web_provider_timeout).fetch(
                    lambda provider: self._fetch_web_provider(provider, query)
                )
            else:
                sources = await call()
        except (TypeError, AttributeError, KeyError) as error:
            # The supplied parsers assume provider JSON shapes. Translate only
            # at this external boundary; internal programming errors still surface.
            raise ValueError("Source returned an invalid response structure") from error
        debug_payload(log, "retrieved_sources", "\n".join(source.model_dump_json() for source in sources))
        info_payload(log, "fetch_output", "\n".join(source.title for source in sources))
        return sources

    async def _fetch_web_provider(self, provider: str, query: str) -> list[Source]:
        """Isolate adapter selection from process-global environment changes."""
        @retry(self.settings)
        async def call() -> list[Source]:
            await self.web_limiter.acquire(provider + ".com")
            request = SynthesisRequest(
                question=query, sources=[], operation="web", max_results=self.settings.max_results,
                web_provider=cast(Literal["tavily", "serper", "duckduckgo"], provider),
            )
            return SourceBatch.model_validate_json(await self._worker(request)).sources
        return await call()

    async def _worker(self, request: SynthesisRequest) -> bytes:
        """Run blocking provider code with cancellation-safe process cleanup."""
        process = subprocess.Popen(
            [sys.executable, "-m", "researcher.worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        try:
            stdout, _ = await asyncio.to_thread(process.communicate, request.model_dump_json().encode())
        finally:
            if process.poll() is None:
                process.kill()
                await asyncio.to_thread(process.wait)
        if process.returncode:
            try:
                error = json.loads(stdout)
            except (ValueError, UnicodeError):
                raise ProviderError("Provider worker failed") from None
            status = error.get("status")
            if isinstance(status, int) and 400 <= status < 500 and status != 429:
                raise ValueError("Provider rejected the request; check model and credentials.")
            raise ProviderError("Provider unavailable")
        return stdout

    async def synthesize(self, question: str, sources: list[Source]) -> AnswerWithCitations:
        """Isolate blocking SDK calls so cancellation also stops provider work."""
        started = time.perf_counter()
        info_payload(log, "synthesis_input", question)

        @retry(self.settings)
        async def call() -> AnswerWithCitations:
            if not self.offline:
                # UTF-8 byte count plus prompt/output allowance is a deliberately
                # conservative estimate, not provider-reported token usage.
                estimate = len(question.encode("utf-8")) + 6144 + sum(
                    len((s.title + s.url + s.snippet[:600]).encode("utf-8")) for s in sources
                )
                await self.token_budget.acquire(estimate)
            request = SynthesisRequest(question=question, sources=sources, offline=self.offline)
            result = AnswerWithCitations.model_validate_json(await self._worker(request))
            try:
                return validate_answer(result, sources, question)
            except ValueError as error:
                # Regenerate within the existing attempt and deadline budgets.
                # Never attach invented citations to an unsupported sentence.
                raise ProviderError("Model returned invalid citations; regeneration required") from error

        try:
            async with asyncio.timeout(self.settings.synthesis_timeout):
                result = await call()
                debug_payload(log, "synthesis_output", result.model_dump_json())
                info_payload(log, "synthesis_output", result.answer)
                log.info(
                    "synthesis_complete sources=%d chars=%d elapsed=%.3f",
                    len(sources),
                    len(result.answer),
                    time.perf_counter() - started,
                )
                return result
        except TimeoutError:
            raise TimeoutError("Synthesis deadline exceeded; worker stopped.") from None
