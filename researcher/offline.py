"""Explicit synthetic fixtures: reproducible demos, never live research."""

import asyncio
import json
import re
from typing import Any

import httpx

from ai.providers.base import LLMProvider
from ai.schemas import Source
from ai.sources import WebSearchProvider

# Educational summaries authored for the demo; URLs identify simulated records.
TOPICS = {
    "photosynthesis": (
        "Photosynthesis",
        [
            "Photosynthesis converts light energy into chemical energy in photosynthetic organisms",
            "Light-dependent reactions generate ATP and NADPH and release oxygen from water",
            "The Calvin cycle uses ATP and NADPH to fix carbon dioxide into carbohydrates",
        ],
    ),
    "transformer": (
        "Long-context transformers",
        [
            "Self-attention relates tokens throughout the available context window",
            "Dense attention has quadratic attention-score cost as sequence length grows",
            "Sparse attention and positional-encoding adaptations can extend useful context, with accuracy and memory trade-offs",
        ],
    ),
    "2008": (
        "The 2008 financial crisis",
        [
            "Risky mortgage lending and falling housing prices increased mortgage defaults",
            "Securitization and high leverage transmitted mortgage losses through financial institutions",
            "Uncertainty about counterparties and funding runs amplified the financial crisis",
        ],
    ),
    "fusion": (
        "Fusion research - educational snapshot",
        [
            "Fusion research studies how light nuclei can combine and release energy under suitable conditions",
            "Magnetic and inertial confinement are two major experimental approaches",
            "A scientific energy-gain result is distinct from a power plant delivering net electricity to the grid",
        ],
    ),
    "crispr": (
        "CRISPR-Cas9",
        [
            "A guide RNA directs Cas9 toward a complementary DNA sequence near a compatible PAM",
            "Cas9 can cut the DNA strands at the targeted site",
            "Cellular DNA repair can introduce sequence changes or use a supplied repair template",
        ],
    ),
}


def fixture_sources(question: str, origin: str) -> list[Source]:
    """Return only the five documented topics, rejecting arbitrary questions."""
    topic = next((key for key in TOPICS if key in question.lower()), None)
    if topic is None:
        raise ValueError(
            "Offline mode supports the five sample topics only; use live mode for other questions."
        )
    title, sentences = TOPICS[topic]
    index = {"wikipedia": 0, "arxiv": 1, "web": 2}[origin]
    return [
        Source(
            title=f"SIMULATED: {title}",
            url=f"https://example.org/offline/{topic}/{origin}",
            snippet=sentences[index] + ".",
            origin=origin,
        )
    ]


class OfflineLLM(LLMProvider):
    """Deterministic extraction through the provided synthesizer contract."""

    def complete(
        self, prompt: str, *, json_schema: dict[str, Any] | None = None, max_tokens: int = 1024
    ) -> str:
        blocks = re.findall(r"\[(\d+)\] \([^\n]+\n     ([^\n]+)", prompt)
        return " ".join(f"{snippet.rstrip('.')} [{index}]." for index, snippet in blocks)


class OfflineWeb(WebSearchProvider):
    """A delayed fake web adapter injected into ai.fetch_web."""

    async def search(self, query: str, *, max_results: int = 3, client: Any = None) -> list[Source]:
        await asyncio.sleep(0.15)
        return fixture_sources(query, "web")[:max_results]


def offline_transport(question: str) -> httpx.MockTransport:
    """Serve simulated HTTP payloads through the real wiki/arXiv parsers."""

    async def handler(request: httpx.Request) -> httpx.Response:
        from xml.sax.saxutils import escape

        await asyncio.sleep(0.075 if "wikipedia" in request.url.host else 0.15)
        if request.url.path == "/w/api.php":
            source = fixture_sources(question, "wikipedia")[0]
            return httpx.Response(200, json=[question, [source.title], [], []])
        if "wikipedia" in request.url.host:
            source = fixture_sources(question, "wikipedia")[0]
            return httpx.Response(
                200,
                json={
                    "title": source.title,
                    "extract": source.snippet,
                    "content_urls": {"desktop": {"page": source.url}},
                },
            )
        source = fixture_sources(question, "arxiv")[0]
        xml = f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>{escape(source.title)}</title><summary>{escape(source.snippet)}</summary><id>{escape(source.url)}</id></entry></feed>'
        return httpx.Response(200, text=xml)

    return httpx.MockTransport(handler)


def questions() -> list[str]:
    """Load the unchanged course data independently of current directory."""
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "data" / "research_questions.json"
    return [item["text"] for item in json.loads(path.read_text(encoding="utf-8"))["questions"]]
