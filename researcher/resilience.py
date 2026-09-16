"""Retry policy and per-host pacing shared by the HTTP boundary."""

import asyncio
import functools
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import ParamSpec, TypeVar

import httpx

from ai.providers.base import ProviderError
from researcher.config import Settings

P = ParamSpec("P")
T = TypeVar("T")
log = logging.getLogger(__name__)


def transient(error: BaseException) -> bool:
    """Walk wrapped errors so authentication errors are never retried."""
    cause: BaseException | None = error
    while cause is not None:
        if getattr(cause, "retry_exhausted", False):
            return False
        if isinstance(cause, httpx.HTTPStatusError):
            return cause.response.status_code == 429 or cause.response.status_code >= 500
        cause = cause.__cause__
    return isinstance(error, (ProviderError, httpx.TransportError, TimeoutError))


def retry_after(response: httpx.Response) -> float:
    """Support both Retry-After seconds and HTTP dates."""
    value = response.headers.get("Retry-After", "0")
    try:
        return max(0, float(value))
    except ValueError:
        try:
            return max(0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return 0


def retry(settings: Settings) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Apply bounded exponential backoff to an async AI boundary call."""

    def decorate(function: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(function)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            for attempt in range(settings.attempts):
                try:
                    return await function(*args, **kwargs)
                except (ProviderError, httpx.HTTPError, TimeoutError) as error:
                    if attempt + 1 == settings.attempts or not transient(error):
                        raise
                    delay = settings.backoff * 2**attempt
                    log.warning(
                        "ai_retry attempt=%d delay=%.3f error_type=%s",
                        attempt + 1,
                        delay,
                        type(error).__name__,
                    )
                    await asyncio.sleep(delay)
            raise RuntimeError("Retry budget exhausted")

        return wrapped

    return decorate


class RateLimiter:
    """One request per host per interval; a bucket with capacity one."""

    def __init__(self, interval: float, arxiv_interval: float) -> None:
        self.interval, self.arxiv_interval = interval, arxiv_interval
        self.locks: dict[str, asyncio.Lock] = {}
        self.next_at: dict[str, float] = {}

    async def acquire(self, host: str) -> None:
        """Wait before dispatch without blocking the event loop."""
        async with self.locks.setdefault(host, asyncio.Lock()):
            await asyncio.sleep(max(0, self.next_at.get(host, 0) - time.monotonic()))
            interval = self.arxiv_interval if host.endswith("arxiv.org") else self.interval
            self.next_at[host] = time.monotonic() + interval


class RetryTransport(httpx.AsyncBaseTransport):
    """Retry every HTTP request, including Wikipedia summary subrequests."""

    def __init__(
        self,
        settings: Settings,
        inner: httpx.AsyncBaseTransport | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        self.settings = settings
        self.inner = inner or httpx.AsyncHTTPTransport()
        self.limiter = limiter or RateLimiter(settings.rate_interval, settings.arxiv_interval)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Handle transient failures; preserve permanent HTTP failures."""
        # The shipped arXiv URL is HTTP; upgrade at the transport boundary.
        if request.url.host == "export.arxiv.org" and request.url.scheme == "http":
            request.url = request.url.copy_with(scheme="https")
        for attempt in range(self.settings.attempts):
            await self.limiter.acquire(request.url.host)
            response = None
            try:
                response = await self.inner.handle_async_request(request)
                # A request is not successful until its body has been received.
                # Read here so dropped body streams also enter the retry policy.
                await response.aread()
                if response.status_code != 429 and response.status_code < 500:
                    return response
                error = httpx.HTTPStatusError("Transient HTTP failure", request=request, response=response)
                if attempt + 1 == self.settings.attempts:
                    setattr(error, "retry_exhausted", True)
                    await response.aclose()
                    raise error
            except httpx.TransportError as error:
                if response is not None:
                    await response.aclose()
                if attempt + 1 == self.settings.attempts:
                    setattr(error, "retry_exhausted", True)
                    raise
            delay = max(self.settings.backoff * 2**attempt, retry_after(response) if response else 0)
            if response:
                await response.aclose()
            log.warning("http_retry host=%s attempt=%d delay=%.3f", request.url.host, attempt + 1, delay)
            await asyncio.sleep(delay)
        raise RuntimeError("HTTP retry budget exhausted")

    async def aclose(self) -> None:
        """Release the shared underlying connection pool."""
        await self.inner.aclose()
