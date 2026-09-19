"""Offline verification of optional fallback setup and service routing."""

from unittest.mock import AsyncMock

import httpx
import pytest
from dotenv import dotenv_values

from ai.providers.base import ProviderError
from researcher import setup_fallback
from researcher.config import Settings
from researcher.service import AIService
from researcher.worker import SourceBatch


def test_fallback_setup_preserves_gemini_and_hides_secret(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(setup_fallback, "__file__", str(tmp_path / "researcher" / "setup_fallback.py"))
    target = tmp_path / ".env"
    target.write_text("GOOGLE_API_KEY=existing-test-key\nLLM_MODEL=existing-model\n", encoding="utf-8")
    monkeypatch.setattr(setup_fallback.getpass, "getpass", lambda _: "test-serper-secret")
    setup_fallback.main()
    values = dotenv_values(target)
    assert values["GOOGLE_API_KEY"] == "existing-test-key"
    assert values["LLM_MODEL"] == "existing-model"
    assert values["SERPER_API_KEY"] == "test-serper-secret"
    assert values["WEB_SEARCH_PROVIDER"] == "duckduckgo"
    assert values["RESEARCH_WEB_FALLBACKS"] == "serper"
    assert "test-serper-secret" not in capsys.readouterr().out


@pytest.mark.parametrize("secret", ["", "has space"])
def test_invalid_fallback_key_does_not_change_env(monkeypatch, tmp_path, secret):
    monkeypatch.setattr(setup_fallback, "__file__", str(tmp_path / "researcher" / "setup_fallback.py"))
    target = tmp_path / ".env"
    target.write_text("LLM_MODEL=keep\n", encoding="utf-8")
    monkeypatch.setattr(setup_fallback.getpass, "getpass", lambda _: secret)
    with pytest.raises(ValueError):
        setup_fallback.main()
    assert target.read_text(encoding="utf-8") == "LLM_MODEL=keep\n"


@pytest.mark.asyncio
async def test_duckduckgo_failure_routes_to_serper(sample_sources):
    settings = Settings(web_search_provider="duckduckgo", web_fallbacks="serper", attempts=1, rate_interval=0)
    service = AIService(settings)
    worker = AsyncMock(side_effect=[
        ProviderError("injected primary failure"),
        SourceBatch(sources=sample_sources).model_dump_json().encode(),
    ])
    service._worker = worker
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        assert await service.fetch("web", "What is photosynthesis?", client) == sample_sources
    assert [call.args[0].web_provider for call in worker.await_args_list] == ["duckduckgo", "serper"]
