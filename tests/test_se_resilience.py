"""Offline HTTP retries, rate pacing and permanent-failure behavior."""

import asyncio
import time

import httpx
import pytest

from ai.providers.base import ProviderError
from researcher.config import Settings
from researcher.resilience import RateLimiter, RetryTransport, retry, retry_after, transient


@pytest.mark.asyncio
async def test_http_retry(respx_mock):
    route = respx_mock.get("https://example.org/test").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(503),
            httpx.Response(200, text="ok"),
        ]
    )
    settings = Settings(backoff=0, rate_interval=0)
    async with httpx.AsyncClient(transport=RetryTransport(settings)) as client:
        assert (await client.get("https://example.org/test")).text == "ok"
    assert route.call_count == 3


@pytest.mark.asyncio
async def test_no_retry_auth(respx_mock):
    route = respx_mock.get("https://example.org/test").respond(401)
    async with httpx.AsyncClient(transport=RetryTransport(Settings())) as client:
        assert (await client.get("https://example.org/test")).status_code == 401
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_http_exhausted(respx_mock):
    route = respx_mock.get("https://example.org/test").respond(503)
    async with httpx.AsyncClient(transport=RetryTransport(Settings(backoff=0, rate_interval=0))) as client:
        with pytest.raises(httpx.HTTPStatusError) as error:
            await client.get("https://example.org/test")
    assert route.call_count == 3
    assert not transient(error.value)


@pytest.mark.asyncio
async def test_network_retry(respx_mock):
    route = respx_mock.get("https://example.org/test").mock(side_effect=httpx.ConnectError("offline"))
    async with httpx.AsyncClient(transport=RetryTransport(Settings(backoff=0, rate_interval=0))) as client:
        with pytest.raises(httpx.ConnectError):
            await client.get("https://example.org/test")
    assert route.call_count == 3


@pytest.mark.asyncio
async def test_ai_backoff(monkeypatch):
    delays = []
    calls = 0

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setattr("researcher.resilience.asyncio.sleep", sleep)

    @retry(Settings(backoff=0.5))
    async def operation():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ProviderError("unavailable")
        return 42

    assert await operation() == 42
    assert delays == [0.5, 1.0]


@pytest.mark.asyncio
async def test_pacing():
    limiter = RateLimiter(0.03, 0.04)
    start = time.monotonic()
    await asyncio.gather(*(limiter.acquire("example.org") for _ in range(3)))
    assert time.monotonic() - start >= 0.055


@pytest.mark.parametrize(
    "header,expected", [("2", 2), ("-1", 0), ("nonsense", 0), ("Wed, 21 Oct 2015 07:28:00 GMT", 0)]
)
def test_retry_header(header, expected):
    assert retry_after(httpx.Response(429, headers={"Retry-After": header})) == expected


@pytest.mark.asyncio
async def test_wikipedia_summary_retried(respx_mock):
    import ai

    respx_mock.get("https://en.wikipedia.org/w/api.php").respond(200, json=["q", ["Example"], [], []])
    summary = respx_mock.get("https://en.wikipedia.org/api/rest_v1/page/summary/Example").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"title": "Example", "extract": "Evidence."}),
        ]
    )
    async with httpx.AsyncClient(transport=RetryTransport(Settings(backoff=0, rate_interval=0))) as client:
        sources = await ai.fetch_wikipedia("q", client=client)
    assert sources[0].snippet == "Evidence."
    assert summary.call_count == 2


def test_external_socket_blocked():
    import socket

    with socket.socket() as connection:
        with pytest.raises(AssertionError, match="external"):
            connection.connect(("8.8.8.8", 443))


@pytest.mark.asyncio
async def test_retry_dropped_response_body():
    class BrokenBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b"partial"
            raise httpx.ReadError("connection dropped during body")

    attempts = 0

    async def handler(request):
        nonlocal attempts
        attempts += 1
        return (
            httpx.Response(200, stream=BrokenBody())
            if attempts == 1
            else httpx.Response(200, text="complete")
        )

    settings = Settings(backoff=0, rate_interval=0)
    async with httpx.AsyncClient(transport=RetryTransport(settings, httpx.MockTransport(handler))) as client:
        response = await client.get("https://example.org/body")
    assert response.text == "complete"
    assert attempts == 2
