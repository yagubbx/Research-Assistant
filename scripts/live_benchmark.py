"""Explicit opt-in network benchmark; excluded from the offline test suite."""

import asyncio
import json
from pathlib import Path
import platform
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from researcher.cache import MemoryCache
from researcher.config import Settings
from researcher.core import Researcher
from researcher.service import AIService


async def main() -> None:
    """Compare real, keyless retrieval for five topical search queries."""
    queries = ["photosynthesis", "transformer", "financial crisis", "fusion energy", "CRISPR"]
    timings = {}
    outcomes = {}
    for mode in ("sequential", "parallel"):
        settings = Settings.from_env()
        app = Researcher(settings, MemoryCache(), AIService(settings))
        start = time.perf_counter()
        results = []
        for query in queries:
            sources = await app.retrieve(query, ["wiki", "arxiv"], no_cache=True, sequential=mode == "sequential")
            results.append({"query": query, "sources": [s.model_dump() for s in sources]})
        timings[mode] = time.perf_counter() - start
        outcomes[mode] = results
    failed = sum(s["status"] != "ok" for rows in outcomes.values() for r in rows for s in r["sources"])
    result = {
        "scope": "Live Wikipedia/arXiv retrieval, five topical queries, one repetition; excludes web and synthesis",
        "python": platform.python_version(), "cache": "all reads/writes bypassed", "pacing": "configured; unchanged in both modes",
        "seconds": timings, "failed_or_empty": failed,
        "speedup": timings["sequential"] / timings["parallel"] if not failed else None,
        "outcomes": outcomes,
    }
    target = Path(__file__).resolve().parent.parent / "artefacts/live-benchmark.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "outcomes"}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
