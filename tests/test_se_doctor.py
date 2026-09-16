"""Local readiness diagnostics must never expose credential values."""

import pytest

from researcher.cli import main
from researcher.config import Settings
from researcher.doctor import diagnose, render_health


def test_offline_needs_no_optional_provider(monkeypatch):
    monkeypatch.setattr("researcher.doctor.importlib.util.find_spec", lambda name: None)
    report = diagnose(Settings(), True, ["wiki"])
    assert report.ready
    assert "Local checks only" in render_health(report)


def test_missing_key_and_sdk(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setattr("researcher.doctor.importlib.util.find_spec", lambda name: None)
    report = diagnose(Settings(), False, ["wiki"])
    assert not report.ready
    assert len(report.issues) == 2


def test_does_not_echo_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-must-stay-private")
    monkeypatch.setattr("researcher.doctor.importlib.util.find_spec", lambda name: object())
    report = diagnose(Settings(), False, ["wiki"])
    assert report.ready
    assert "test-key-must-stay-private" not in report.model_dump_json()


def test_missing_google_namespace(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-only")

    def missing(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("researcher.doctor.importlib.util.find_spec", missing)
    assert not diagnose(Settings(llm_provider="gemini"), False, ["wiki"]).ready


@pytest.mark.parametrize("json_flag", [[], ["--json"]])
def test_doctor_cli(json_flag, capsys):
    assert main(["doctor", "--offline", *json_flag]) == 0
    assert "offline" in capsys.readouterr().out


def test_live_doctor_nonzero(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert main(["doctor", "--sources", "wiki"]) == 2
