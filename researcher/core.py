"""Concurrent retrieval with independent failure domains and shared HTTP."""

import asyncio
import logging
import time
from typing import cast

import httpx

from ai.providers.base import ProviderError
from researcher.cache import Cache
from researcher.config import Settings
from researcher.logging_config import debug_payload
from researcher.models import ResearchSession, SourceName, SourceResult
from researcher.offline import fixture_sources, offline_transport
from researcher.resilience import RateLimiter, RetryTransport
from researcher.service import AIService
from researcher.validation import parse_sources, valid_sources, validate_answer, validate_question

log = logging.getLogger(__name__)


class Researcher:
    """Own a bounded pipeline, cache repository and AI service."""

    def __init__(self, settings: Settings, cache: Cache, service: AIService) -> None:
        self.settings, self.cache, self.service = settings, cache, service
        self.semaphore = asyncio.Semaphore(settings.concurrency)
        self.limiter = RateLimiter(settings.rate_interval, settings.arxiv_interval)

    async def retrieve(
        self, question: str, names: list[str], *, no_cache: bool = False, sequential: bool = False
    ) -> list[SourceResult]:
        """Fetch a chosen subset; compare scheduling with identical code paths."""
        question = validate_question(question, self.settings.max_question_length)
        names = parse_sources(",".join(names))
        transport = RetryTransport(
            self.settings, offline_transport(question) if self.service.offline else None, self.limiter
        )
        async with httpx.AsyncClient(
            transport=transport,
            timeout=self.settings.http_timeout,
            follow_redirects=True,
            headers={"User-Agent": "CourseResearchAssistant/1.0 (educational project)"},
        ) as client:

            async def one(name: str) -> SourceResult:
                started = time.perf_counter()
                result = SourceResult(name=cast(SourceName, name), status="failed")
                try:
                    async with asyncio.timeout(self.settings.source_timeout):
                        async with self.semaphore:
                            cached = (
                                None if no_cache else await asyncio.to_thread(self.cache.get, name, question)
                            )
                            if cached is not None:
                                result.sources = valid_sources(cached)
                                result.status = "cached" if result.sources else "empty"
                            else:
                                result.sources = valid_sources(
                                    await self.service.fetch(name, question, client)
                                )
                                result.status = "ok" if result.sources else "empty"
                                if result.sources and not no_cache:
                                    await asyncio.to_thread(self.cache.put, name, question, result.sources)
                            if not result.sources:
                                result.note = "No usable evidence returned."
                except TimeoutError:
                    result.status, result.note = "timeout", "Source deadline exceeded."
                except (ProviderError, httpx.HTTPError, ValueError, OSError) as error:
                    result.note = f"Source unavailable ({type(error).__name__})."
                result.elapsed = time.perf_counter() - started
                log.info(
                    "source_complete source=%s status=%s count=%d elapsed=%.3f",
                    name,
                    result.status,
                    len(result.sources),
                    result.elapsed,
                )
                return result

            if sequential:
                return [await one(name) for name in names]
            outcomes = await asyncio.gather(*(one(name) for name in names), return_exceptions=True)
            results = []
            for outcome in outcomes:
                if isinstance(outcome, BaseException):
                    raise outcome
                results.append(outcome)
            return results

    async def ask(self, question: str, names: list[str], *, no_cache: bool = False) -> ResearchSession:
        """Produce a validated cited answer, or a clear actionable failure."""
        started = time.perf_counter()
        question = validate_question(question, self.settings.max_question_length)
        names = parse_sources(",".join(names))
        if self.service.offline:
            fixture_sources(question, "wikipedia")
        else:
            self.settings.check_credentials(names)
        log.info(
            "research_start question_chars=%d sources=%s offline=%s",
            len(question),
            ",".join(names),
            self.service.offline,
        )
        results = await self.retrieve(question, names, no_cache=no_cache)
        debug_payload(log, "research_input", question)
        sources = valid_sources([source for result in results for source in result.sources])
        if not sources:
            raise ValueError(
                "All selected sources returned no usable evidence. Try again or choose other sources."
            )
        answer = validate_answer(await self.service.synthesize(question, sources), sources, question)
        return ResearchSession(
            result=answer,
            retrieval=results,
            elapsed=time.perf_counter() - started,
            offline=self.service.offline,
        )
