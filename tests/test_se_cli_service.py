"""CLI, worker, real offline parsers and cancellation coverage."""

import io
from unittest.mock import AsyncMock

import pytest

from researcher.cli import main, render
from researcher.config import Settings
from researcher.service import AIService
from researcher.worker import SynthesisRequest


@pytest.mark.asyncio
async def test_keyless_provider_isolated(sample_sources, monkeypatch):
    from researcher.worker import SourceBatch

    service = AIService(Settings(web_search_provider="duckduckgo", rate_interval=0))
    worker = AsyncMock(return_value=SourceBatch(sources=sample_sources).model_dump_json().encode())
    monkeypatch.setattr(service, "_worker", worker)
    assert await service.fetch("web", "q", None) == sample_sources
    assert worker.call_args.args[0].operation == "web"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body,error",
    [(b"{}", "ProviderError"), (b'{"status":401}', "ValueError"), (b"not json", "ProviderError")],
)
async def test_worker_error_redacted(sample_sources, monkeypatch, body, error):
    from ai.providers.base import ProviderError

    class FailedProcess:
        returncode = 1

        def communicate(self, data):
            return body, b"secret-provider-detail"

        def poll(self):
            return 1

    monkeypatch.setattr("researcher.service.subprocess.Popen", lambda *args, **kwargs: FailedProcess())
    service = AIService(Settings(attempts=1), offline=True)
    with pytest.raises(ValueError if error == "ValueError" else ProviderError) as result:
        await service.synthesize("q", sample_sources)
    assert "secret" not in str(result.value)


def test_cli_json(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_CACHE_DIR", str(tmp_path))
    assert main(["ask", "photosynthesis", "--offline", "--no-cache", "--json"]) == 0
    assert '"offline": true' in capsys.readouterr().out


def test_cli_bad_input(capsys):
    assert main(["ask", "", "--offline"]) == 2
    assert "Error:" in capsys.readouterr().err


def test_cli_unknown_offline(capsys):
    assert main(["ask", "unrelated question", "--offline"]) == 2
    assert "five sample topics" in capsys.readouterr().err


def test_cli_output(tmp_path):
    output = tmp_path / "answer.txt"
    assert main(["ask", "photosynthesis", "--offline", "--sources", "wiki", "--output", str(output)]) == 0
    assert "References:" in output.read_text()


def test_cli_invalid_settings(monkeypatch):
    monkeypatch.setenv("RESEARCH_ATTEMPTS", "secret-invalid-value")
    assert main(["ask", "photosynthesis", "--offline"]) == 2


def test_worker(sample_sources, monkeypatch):
    from researcher.worker import main as worker_main

    request = SynthesisRequest(question="q", sources=sample_sources, offline=True)
    monkeypatch.setattr("sys.stdin", io.StringIO(request.model_dump_json()))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    assert worker_main() == 0


def test_worker_invalid(monkeypatch):
    from researcher.worker import main as worker_main

    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    assert worker_main() == 1


@pytest.mark.asyncio
async def test_service_unknown_source():
    service = AIService(Settings(), offline=True)
    with pytest.raises(ValueError):
        await service.fetch("invalid", "q", None)


@pytest.mark.asyncio
async def test_synthesis_hard_timeout(sample_sources):
    service = AIService(Settings(synthesis_timeout=0.001), offline=True)
    with pytest.raises(TimeoutError, match="worker stopped"):
        await service.synthesize("q", sample_sources)


@pytest.mark.asyncio
async def test_render_degradation(app=None):
    from researcher.cache import MemoryCache
    from researcher.core import Researcher

    service = AIService(Settings(rate_interval=0, arxiv_interval=0), offline=True)
    original = service.fetch

    async def fetch(name, query, client):
        if name == "arxiv":
            raise TimeoutError()
        return await original(name, query, client)

    service.fetch = AsyncMock(side_effect=fetch)
    app = Researcher(service.settings, MemoryCache(), service)
    result = await app.ask("photosynthesis", ["wiki", "arxiv"])
    assert "Note - arxiv" in render(result)
