"""Structured stderr diagnostics with safe, fixed-format event messages."""

import json
import logging
import os
import re


def redact(payload: str) -> str:
    """Mask configured API keys and conventional credential assignments."""
    keys = (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "LLM_API_KEY",
        "TAVILY_API_KEY",
        "SERPER_API_KEY",
    )
    secrets = sorted({os.environ[key] for key in keys if os.environ.get(key)}, key=len, reverse=True)
    for secret in secrets:
        payload = payload.replace(secret, "[REDACTED]")
    payload = re.sub(
        r"(?i)((?:api[_-]?key|access_token|authorization)\s*[=:]\s*)[^\s&\"']+", r"\1[REDACTED]", payload
    )
    return payload


def info_payload(logger: logging.Logger, event: str, payload: str) -> None:
    """Record a short redacted input/output preview required by the brief."""
    logger.info("%s preview=%s", event, redact(payload)[:200])


def debug_payload(logger: logging.Logger, event: str, payload: str) -> None:
    """Log full diagnostic payloads only at the explicitly selected DEBUG level."""
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s payload=%s", event, redact(payload))


class JsonFormatter(logging.Formatter):
    """Machine-readable log records without arbitrary provider payloads."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {"level": record.levelname, "logger": record.name, "event": record.getMessage()},
            ensure_ascii=True,
        )


def configure_logging(level: str) -> None:
    """Keep results on stdout and redacted operational events on stderr."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("researcher")
    root.handlers = [handler]
    root.setLevel(level)
    root.propagate = False
    logging.getLogger("httpx").setLevel(logging.WARNING)
