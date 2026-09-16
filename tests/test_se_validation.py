"""Input, provenance and configuration safety tests."""

import pytest

from ai.schemas import AnswerWithCitations, Source
from researcher.config import Settings
from researcher.validation import (
    canonical_query,
    clean_text,
    parse_sources,
    valid_sources,
    validate_answer,
    validate_question,
)


@pytest.mark.parametrize("value", ["", "   ", "???", "\x1b[31m"])
def test_empty_input(value):
    with pytest.raises(ValueError):
        validate_question(value)


def test_size_limit():
    with pytest.raises(ValueError):
        validate_question("a" * 2001)


def test_normalization():
    assert canonical_query(" WHAT IS PHOTOSYNTHESIS? ") == canonical_query("what is photosynthesis")
    assert canonical_query("C++") != canonical_query("C")


def test_terminal_safety():
    assert clean_text("\x1b[31m<b>hello</b>\u202e\nworld") == "hello world"


@pytest.mark.parametrize("value", ["", "wiki,", "reddit", "wiki,web,unknown"])
def test_invalid_sources(value):
    with pytest.raises(ValueError):
        parse_sources(value)


def test_source_selection():
    assert parse_sources(" WEB, wiki,web") == ["web", "wiki"]


def test_safe_evidence(sample_sources):
    unsafe = Source(title="x", snippet="y", url="javascript:alert(1)", origin="web")
    assert valid_sources([unsafe] + sample_sources + sample_sources) == sample_sources


def test_reference_url_rejects_bidi_control():
    source = Source(title="unsafe", snippet="evidence", url="https://example.org/\u202eabc", origin="web")
    assert valid_sources([source]) == []


def test_citation_repair(sample_sources):
    result = validate_answer(
        AnswerWithCitations(question="q", answer="Evidence [1,99]."), sample_sources, "q"
    )
    assert result.answer == "Evidence [1]."
    assert [c.index for c in result.citations] == [1]


@pytest.mark.parametrize("answer", ["", "Invented claim.", "Invented [99].", "Cited [1]. Uncited fact."])
def test_bad_answer(answer, sample_sources):
    with pytest.raises(ValueError):
        validate_answer(AnswerWithCitations(question="q", answer=answer), sample_sources, "q")


def test_env_settings(monkeypatch):
    monkeypatch.setenv("RESEARCH_CONCURRENCY", "2")
    assert Settings.from_env().concurrency == 2


def test_env_invalid(monkeypatch):
    monkeypatch.setenv("RESEARCH_CONCURRENCY", "0")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_missing_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        Settings().check_credentials(["wiki"])


def test_valid_keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only")
    monkeypatch.setenv("TAVILY_API_KEY", "test-only")
    Settings().check_credentials(["web"])


def test_debug_payload_redacts_keys(monkeypatch, caplog):
    import logging

    from researcher.logging_config import debug_payload

    monkeypatch.setenv("OPENAI_API_KEY", "private-test-key")
    logger = logging.getLogger("test.redaction")
    with caplog.at_level(logging.DEBUG, logger=logger.name):
        debug_payload(logger, "response", "Evidence private-test-key api_key=another-secret")
    assert "private-test-key" not in caplog.text
    assert "another-secret" not in caplog.text
    assert "[REDACTED]" in caplog.text


def test_debug_payload_is_opt_in(caplog):
    import logging

    from researcher.logging_config import debug_payload

    logger = logging.getLogger("test.default-log")
    with caplog.at_level(logging.INFO, logger=logger.name):
        debug_payload(logger, "response", "private-question")
    assert "private-question" not in caplog.text


def test_info_preview_redacts_before_truncating(monkeypatch, caplog):
    import logging

    from researcher.logging_config import info_payload

    monkeypatch.setenv("GOOGLE_API_KEY", "test-secret-value")
    logger = logging.getLogger("test.info-preview")
    with caplog.at_level(logging.INFO, logger=logger.name):
        info_payload(logger, "input", "test-secret-value " + "a" * 500)
    message = caplog.records[-1].getMessage()
    assert "test-secret-value" not in message
    assert "[REDACTED]" in message
    assert len(message.split("preview=", 1)[1]) == 200
