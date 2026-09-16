"""Ordered web-provider recovery and a bounded sliding token window."""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable

import httpx

from ai.providers.base import ProviderError
from ai.schemas import Source

log = logging.getLogger(__name__)


class FailoverProvider:
    """Try configured web adapters in order, each within its own deadline."""

    def __init__(self, providers: list[str], timeout: float) -> None:
        if not providers or timeout <= 0:
            raise ValueError("Providers and a positive deadline are required.")
        self.providers = list(dict.fromkeys(providers))
        self.timeout = timeout

    async def fetch(self, call: Callable[[str], Awaitable[list[Source]]]) -> list[Source]:
        """Do not swallow cancellation; redact upstream failure details."""
        for name in self.providers:
            try:
                async with asyncio.timeout(self.timeout):
                    result = await call(name)
                if not result:
                    raise ProviderError("Provider returned no evidence")
                log.info("web_provider_selected provider=%s", name)
                return result
            except (ProviderError, httpx.HTTPError, TimeoutError, ValueError, OSError) as error:
                log.warning("web_provider_failed provider=%s error_type=%s", name, type(error).__name__)
        raise ProviderError("All configured web providers failed")


class TokenBudget:
    """Reserve estimated tokens before dispatch; failed calls keep reservations.

    Local to a service instance, not an account-wide billing/quota counter.
    """

    def __init__(self, tokens_per_minute: int, window: float = 60) -> None:
        if tokens_per_minute <= 0 or window <= 0:
            raise ValueError("Token budget and window must be positive.")
        self.limit, self.window = tokens_per_minute, window
        self.events: deque[tuple[float, int]] = deque()
        self.lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int) -> None:
        """Wait for sliding-window capacity, or reject an impossible request."""
        if not 0 < estimated_tokens <= self.limit:
            raise ValueError("Request exceeds the configured token budget; shorten evidence or raise TPM.")
        while True:
            async with self.lock:
                now = time.monotonic()
                while self.events and self.events[0][0] <= now - self.window:
                    self.events.popleft()
                if sum(tokens for _, tokens in self.events) + estimated_tokens <= self.limit:
                    self.events.append((now, estimated_tokens))
                    return
                delay = max(0.001, self.window - (now - self.events[0][0]))
            log.info("token_budget_wait seconds=%.3f estimated_tokens=%d", delay, estimated_tokens)
            await asyncio.sleep(delay)
