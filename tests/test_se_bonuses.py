"""Fault injection and virtual-time budget tests; never contact providers."""

import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from ai.providers.base import ProviderError
from researcher.bonuses import FailoverProvider, TokenBudget
from researcher.cache import MemoryCache
from researcher.config import Settings
from researcher.core import Researcher
from researcher.service import AIService
from researcher.worker import SourceBatch


@pytest.mark.asyncio
async def test_failover_primary_failure_secondary_succeeds(sample_sources):
    call = AsyncMock(side_effect=[ProviderError("down"), sample_sources])
    assert await FailoverProvider(["tavily", "duckduckgo"], 1).fetch(call) == sample_sources
    assert [c.args[0] for c in call.await_args_list] == ["tavily", "duckduckgo"]


@pytest.mark.asyncio
async def test_failover_primary_success_skips_secondary(sample_sources):
    call = AsyncMock(return_value=sample_sources)
    await FailoverProvider(["tavily", "duckduckgo"], 1).fetch(call)
    assert call.await_count == 1


@pytest.mark.asyncio
async def test_failover_timeout(sample_sources):
    async def call(name):
        if name == "tavily":
            await asyncio.sleep(1)
        return sample_sources
    assert await FailoverProvider(["tavily", "duckduckgo"], .01).fetch(call) == sample_sources


@pytest.mark.asyncio
async def test_failover_all_failed_redacts():
    with pytest.raises(ProviderError, match="All configured"):
        await FailoverProvider(["tavily"], 1).fetch(AsyncMock(side_effect=ProviderError("secret")))


@pytest.mark.asyncio
async def test_failover_empty_result(sample_sources):
    call = AsyncMock(side_effect=[[], sample_sources])
    assert await FailoverProvider(["tavily", "duckduckgo"], 1).fetch(call) == sample_sources


@pytest.mark.asyncio
async def test_failover_cancellation_propagates():
    with pytest.raises(asyncio.CancelledError):
        await FailoverProvider(["tavily"], 1).fetch(AsyncMock(side_effect=asyncio.CancelledError))


@pytest.mark.asyncio
async def test_token_budget_forces_wait(monkeypatch):
    clock = [100.0]
    waits = []
    monkeypatch.setattr("researcher.bonuses.time.monotonic", lambda: clock[0])
    async def sleep(delay):
        waits.append(delay)
        clock[0] += delay
    monkeypatch.setattr("researcher.bonuses.asyncio.sleep", sleep)
    budget = TokenBudget(10)
    await budget.acquire(7)
    await budget.acquire(4)
    assert waits == [60.0]
    assert list(budget.events) == [(160.0, 4)]


@pytest.mark.asyncio
async def test_token_budget_rejects_oversized():
    with pytest.raises(ValueError, match="exceeds"):
        await TokenBudget(10).acquire(11)


@pytest.mark.asyncio
async def test_token_budget_parallel_capacity():
    budget = TokenBudget(10)
    await asyncio.gather(budget.acquire(4), budget.acquire(6))
    assert sum(n for _, n in budget.events) == 10


@pytest.mark.parametrize("payload", [["q", 123], ["q", ["Title"]]])
@pytest.mark.asyncio
async def test_malformed_wikipedia_degrades_not_crash(monkeypatch, payload):
    def handler(request):
        return httpx.Response(200, json=payload)
    monkeypatch.setattr("researcher.core.RetryTransport", lambda *args: httpx.MockTransport(handler))
    settings = Settings(attempts=1)
    app = Researcher(settings, MemoryCache(), AIService(settings))
    result = await app.retrieve("question", ["wiki"], no_cache=True)
    assert result[0].status == "failed"
    assert result[0].note == "Source unavailable (ValueError)."


@pytest.mark.asyncio
async def test_service_failover_is_wired(sample_sources):
    settings = Settings(web_fallbacks="duckduckgo", attempts=1, rate_interval=0)
    service = AIService(settings)
    service._worker = AsyncMock(side_effect=[ProviderError("down"), SourceBatch(sources=sample_sources).model_dump_json().encode()])
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        assert await service.fetch("web", "question", client) == sample_sources
    assert [c.args[0].web_provider for c in service._worker.await_args_list] == ["tavily", "duckduckgo"]


@pytest.mark.asyncio
async def test_synthesis_reserves_tokens_before_worker(sample_sources):
    service = AIService(Settings(attempts=1, gemini_tpm=1, llm_provider="gemini"))
    service._worker = AsyncMock()
    with pytest.raises(ValueError, match="exceeds"):
        await service.synthesize("question", sample_sources)
    service._worker.assert_not_called()


def test_unknown_fallback_rejected():
    with pytest.raises(ValueError):
        Settings(web_fallbacks="unknown")
