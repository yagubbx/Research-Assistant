"""Typed values exchanged by orchestration, cache and presentation."""

from typing import Literal

from pydantic import BaseModel, Field

from ai.schemas import AnswerWithCitations, Source

SourceName = Literal["wiki", "arxiv", "web"]


class SourceResult(BaseModel):
    """A source's independent outcome, including degraded operation."""

    name: SourceName
    sources: list[Source] = Field(default_factory=list)
    status: Literal["ok", "cached", "empty", "failed", "timeout"]
    elapsed: float = 0
    note: str = ""


class ResearchSession(BaseModel):
    """A complete answer plus provenance and retrieval diagnostics."""

    result: AnswerWithCitations
    retrieval: list[SourceResult]
    elapsed: float
    offline: bool = False


class CacheEntry(BaseModel):
    """Versioned disk record; expiry uses wall-clock Unix seconds."""

    version: Literal[1] = 1
    expires_at: float
    sources: list[Source]
