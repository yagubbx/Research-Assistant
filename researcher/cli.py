"""Command-line application and reproducible five-question benchmark."""

import argparse
import asyncio
import json
import logging
import platform
import statistics
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from ai.providers.base import ProviderError
from researcher.cache import JsonCache
from researcher.config import Settings
from researcher.core import Researcher
from researcher.doctor import diagnose, render_health
from researcher.logging_config import configure_logging
from researcher.models import ResearchSession
from researcher.offline import questions
from researcher.service import AIService
from researcher.validation import parse_sources


def render(session: ResearchSession) -> str:
    """Preserve numeric references and explicitly show missing sources."""
    lines = ["OFFLINE DEMO: synthetic evidence; not live research.\n"] if session.offline else []
    lines += [f"Q: {session.result.question}", "", session.result.answer, "", "References:"]
    for citation in session.result.citations:
        lines.extend(
            [
                f"  [{citation.index}] ({citation.source.origin}) {citation.source.title}",
                f"      {citation.source.url}",
            ]
        )
    for source in session.retrieval:
        if source.note:
            lines.append(f"  Note - {source.name}: {source.note}")
    lines += [
        "",
        "Retrieval: " + ", ".join(f"{s.name}={s.status} ({s.elapsed:.3f}s)" for s in session.retrieval),
        f"Total: {session.elapsed:.3f}s",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Expose required ask flags and portable demonstration commands."""
    parser = argparse.ArgumentParser(prog="researcher", description="Research questions with cited evidence.")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("ask", "demo", "benchmark", "doctor"):
        sub = commands.add_parser(command)
        if command == "ask":
            sub.add_argument("question")
        sub.add_argument(
            "--offline",
            action="store_true",
            help="Use explicitly simulated sample evidence; no network or keys",
        )
        sub.add_argument("--sources", default="wiki,arxiv,web")
        sub.add_argument("--no-cache", action="store_true")
        sub.add_argument("--output", type=Path)
        sub.add_argument("--json", action="store_true")
        if command == "benchmark":
            sub.add_argument("--repeats", type=int, default=3)
    return parser


async def execute(args: argparse.Namespace, settings: Settings) -> str:
    """Run commands through one shared composition root."""
    names = parse_sources(args.sources)
    if args.offline:
        settings = settings.model_copy(update={"rate_interval": 0, "arxiv_interval": 0})
    namespace = (
        "offline-v1" if args.offline else (
            f"live-v1-{settings.web_search_provider}-{settings.web_fallbacks}-{settings.max_results}"
        )
    )
    cache = JsonCache(settings.cache_dir, settings.cache_ttl, namespace)
    app = Researcher(settings, cache, AIService(settings, args.offline))
    if args.command == "benchmark":
        if not 1 <= args.repeats <= 20:
            raise ValueError("Repeats must be between 1 and 20.")
        measurements: dict[str, list[float]] = {"sequential": [], "parallel": []}
        statuses: list[str] = []
        for repeat in range(args.repeats):
            order = ["sequential", "parallel"] if repeat % 2 == 0 else ["parallel", "sequential"]
            for mode in order:
                started = time.perf_counter()
                for question in questions():
                    results = await app.retrieve(
                        question, names, no_cache=True, sequential=mode == "sequential"
                    )
                    statuses.extend(result.status for result in results)
                measurements[mode].append(time.perf_counter() - started)
        sequential = statistics.median(measurements["sequential"])
        parallel = statistics.median(measurements["parallel"])
        return json.dumps(
            {
                "mode": "simulated HTTP, 150ms per source, no rate pacing"
                if args.offline
                else "live source HTTP; excludes synthesis",
                "python": platform.python_version(),
                "platform": platform.platform(),
                "questions": 5,
                "sources": names,
                "repeats": args.repeats,
                "cache": "bypassed for reads and writes",
                "concurrency": settings.concurrency,
                "raw_seconds": measurements,
                "median_sequential": sequential,
                "median_parallel": parallel,
                "speedup": sequential / parallel,
                "failed_or_empty": sum(s not in {"ok", "cached"} for s in statuses),
            },
            indent=2,
        )
    selected = [args.question] if args.command == "ask" else questions()
    sessions = [await app.ask(question, names, no_cache=args.no_cache) for question in selected]
    if args.json:
        return (
            sessions[0].model_dump_json(indent=2)
            if args.command == "ask"
            else json.dumps([s.model_dump() for s in sessions], indent=2)
        )
    return "\n\n".join(render(session) for session in sessions)


def main(argv: Sequence[str] | None = None) -> int:
    """Return shell-friendly codes and readable errors without tracebacks."""
    args = build_parser().parse_args(argv)
    try:
        settings = Settings.from_env()
        configure_logging(settings.log_level)
        exit_code = 0
        if args.command == "doctor":
            health = diagnose(settings, args.offline, parse_sources(args.sources))
            output = health.model_dump_json(indent=2) if args.json else render_health(health)
            exit_code = 0 if health.ready else 2
        else:
            output = asyncio.run(execute(args, settings))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output + "\n", encoding="utf-8")
        sys.stdout.write(output + "\n")
        return exit_code
    except (ValueError, OSError, ProviderError, TimeoutError) as error:
        # Validation errors can include input values; never echo full settings.
        from pydantic import ValidationError

        message = (
            "Invalid configuration: check variable types and bounds in .env.example."
            if isinstance(error, ValidationError)
            else str(error)
        )
        if isinstance(error, (OSError, ProviderError)):
            message = f"Operation failed ({type(error).__name__}); check configuration and access."
        logging.getLogger("researcher").error("command_failed error_type=%s", type(error).__name__)
        sys.stderr.write(f"Error: {message}\n")
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("Cancelled.\n")
        return 130
