"""Local secret setup without network calls or real credentials."""

from pathlib import Path

import pytest
from dotenv import dotenv_values

from researcher import setup


def test_setup_preserves_unrelated_values_and_hides_key(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(setup, "__file__", str(tmp_path / "researcher" / "setup.py"))
    env = tmp_path / ".env"
    env.write_text("RESEARCH_CACHE_TTL=55\n", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _: "gemini-2.5-flash")
    monkeypatch.setattr(setup.getpass, "getpass", lambda _: "test-only-not-a-real-key")
    setup.main()
    values = dotenv_values(env)
    assert values["RESEARCH_CACHE_TTL"] == "55"
    assert values["GOOGLE_API_KEY"] == "test-only-not-a-real-key"
    assert values["LLM_PROVIDER"] == "gemini"
    assert "test-only-not-a-real-key" not in capsys.readouterr().out


@pytest.mark.parametrize("value", ["", "has space"])
def test_setup_rejects_invalid_key_before_writing(monkeypatch, tmp_path, value):
    monkeypatch.setattr(setup, "__file__", str(tmp_path / "researcher" / "setup.py"))
    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr(setup.getpass, "getpass", lambda _: value)
    with pytest.raises(ValueError):
        setup.main()
    assert not Path(tmp_path / ".env").exists()
