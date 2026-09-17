"""Search adaptation outside the immutable course AI package."""

import asyncio
import re
from typing import Any

from ai.providers.base import ProviderError
from ai.schemas import Source
from ai.sources import WebSearchProvider


def topic_query(question: str) -> str:
    """Remove a narrow set of English question frames, preserving topic words."""
    value = question.strip().rstrip("? ")
    value = re.sub(r"^(?:what (?:is|are)|explain|describe)\s+", "", value, flags=re.I)
    value = re.sub(r"\s+and (?:what are )?(?:its|their) main stages$", "", value, flags=re.I)
    return value or question


class BoundedWebSearch(WebSearchProvider):
    """Use a bounded backend in the killable provider worker."""

    async def search(self, query: str, *, max_results: int = 3, client: Any = None) -> list[Source]:
        """Return real web evidence or an explicit provider error."""
        def run() -> list[Source]:
            from ddgs import DDGS

            try:
                items = DDGS(timeout=5).text(query, max_results=max_results, backend="bing")
                return [Source(title=item.get("title", "Web result"), url=item["href"],
                               snippet=item.get("body", ""), origin="web")
                        for item in items if item.get("href")]
            except Exception as error:
                raise ProviderError("Web search backend unavailable") from error

        return await asyncio.to_thread(run)
