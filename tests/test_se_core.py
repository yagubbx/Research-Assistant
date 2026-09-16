"""End-to-end and concurrency invariants with injected AI failures."""

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from ai.providers.base import ProviderError
from ai.schemas import AnswerWithCitations
from researcher.cache import MemoryCache
from researcher.config import Settings
from researcher.core import Researcher
from researcher.service import AIService


@pytest.fixture
def app(sample_sources):
    settings = Settings(backoff=0, rate_interval=0, arxiv_interval=0)
    service = AIService(settings, offline=True)
    service.fetch = AsyncMock(return_value=sample_sources)
    service.synthesize = AsyncMock(
        return_value=AnswerWithCitations(question="photosynthesis", answer="A supported statement [1].")
    )
    return Researcher(settings, MemoryCache(), service)


@pytest.mark.asyncio
async def test_happy_path(app):
    session = await app.ask("photosynthesis", ["wiki", "arxiv", "web"])
    assert session.result.citations[0].index == 1
    assert all(r.status == "ok" for r in session.retrieval)
    clients = [call.args[2] for call in app.service.fetch.call_args_list]
    assert all(c is clients[0] for c in clients)


@pytest.mark.asyncio
async def test_failure_degrades(app, sample_sources):
    async def fetch(name, query, client):
        if name == "arxiv":
            raise ProviderError("secret must not appear")
        return sample_sources

    app.service.fetch.side_effect = fetch
    result = await app.ask("photosynthesis", ["wiki", "arxiv", "web"])
    assert result.retrieval[1].status == "failed"
    assert "secret" not in result.model_dump_json()
    assert result.result.citations


@pytest.mark.asyncio
async def test_timeout_degrades(app, sample_sources):
    app.settings.source_timeout = 0.05

    async def fetch(name, query, client):
        if name == "arxiv":
            await asyncio.sleep(1)
        return sample_sources

    app.service.fetch.side_effect = fetch
    result = await app.ask("photosynthesis", ["wiki", "arxiv"])
    assert result.retrieval[1].status == "timeout"


@pytest.mark.asyncio
async def test_all_fail(app):
    app.service.fetch.side_effect = ProviderError("offline")
    with pytest.raises(ValueError, match="All selected"):
        await app.ask("photosynthesis", ["wiki", "web"])
    app.service.synthesize.assert_not_called()


@pytest.mark.asyncio
async def test_cache_bypass(app):
    await app.ask("photosynthesis", ["wiki"])
    second = await app.ask("PHOTOSYNTHESIS?", ["wiki"])
    assert second.retrieval[0].status == "cached"
    assert app.service.fetch.await_count == 1
    await app.ask("photosynthesis", ["wiki"], no_cache=True)
    assert app.service.fetch.await_count == 2


@pytest.mark.asyncio
async def test_concurrency_bound(app, sample_sources):
    app.semaphore = asyncio.Semaphore(2)
    active = peak = 0

    async def fetch(name, query, client):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.04)
        active -= 1
        return sample_sources

    app.service.fetch.side_effect = fetch
    await app.retrieve("q", ["wiki", "arxiv", "web"], no_cache=True)
    assert peak == 2


@pytest.mark.asyncio
async def test_parallel_overlaps(app, sample_sources):
    async def fetch(name, query, client):
        await asyncio.sleep(0.08)
        return sample_sources

    app.service.fetch.side_effect = fetch
    start = time.perf_counter()
    await app.retrieve("q", ["wiki", "arxiv", "web"], no_cache=True, sequential=True)
    sequential = time.perf_counter() - start
    start = time.perf_counter()
    await app.retrieve("q", ["wiki", "arxiv", "web"], no_cache=True)
    assert time.perf_counter() - start < sequential * 0.8


@pytest.mark.asyncio
async def test_empty_and_bad_input(app):
    app.service.fetch.return_value = []
    with pytest.raises(ValueError):
        await app.ask("photosynthesis", ["wiki"])
    with pytest.raises(ValueError):
        await app.ask("", ["wiki"])


@pytest.mark.asyncio
async def test_unexpected_bug_visible(app):
    app.service.fetch.side_effect = TypeError("programming bug")
    with pytest.raises(TypeError):
        await app.retrieve("q", ["wiki"])
