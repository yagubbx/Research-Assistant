"""Synthesize a final answer with bracketed citations from a list of sources."""

from __future__ import annotations

import re

from ai.providers.base import LLMProvider
from ai.providers.factory import get_llm
from ai.schemas import Source, Citation, AnswerWithCitations


_PROMPT_TEMPLATE = """You are a careful research assistant. Answer the user's
question using ONLY the numbered sources below. Do not use outside knowledge
and do not invent sources.

CITATION RULES:
- EVERY factual sentence MUST contain at least one valid inline citation.
- Use source numbers in square brackets, for example [1] or [2,3].
- Put the citation in the SAME sentence as the claim it supports.
- NEVER write a factual sentence without an inline citation.
- Use ONLY source numbers that appear in the Sources section below.
- If the available sources do not support a claim, do not make that claim.
- If the sources do not contain enough information to answer the question,
  say so and cite the source(s) that support what can be stated.

Question:
{question}

Sources:
{source_block}

Write a concise answer of 3-6 sentences.
Before returning the answer, verify that EVERY sentence containing factual
information includes at least one valid [N] citation.
Do not list the sources at the end; they are handled separately.
"""


def _format_source_block(sources: list[Source]) -> str:
    lines: list[str] = []
    for i, src in enumerate(sources, start=1):
        lines.append(
            f"[{i}] ({src.origin}) {src.title} — {src.url}\n"
            f"     {src.snippet[:600]}"
        )
    return "\n\n".join(lines)


_CITATION_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def _extract_cited_indices(answer: str, n_sources: int) -> list[int]:
    """Pull the unique 1-based indices that the answer actually cites.

    Drops anything out of range so we don't ship dangling citations.
    """
    used: set[int] = set()
    for m in _CITATION_RE.finditer(answer):
        for piece in m.group(1).split(","):
            try:
                idx = int(piece.strip())
            except ValueError:
                continue
            if 1 <= idx <= n_sources:
                used.add(idx)
    return sorted(used)


def synthesize(
    question: str,
    sources: list[Source],
    *,
    llm: LLMProvider | None = None,
) -> AnswerWithCitations:
    """Use the LLM to write an answer that cites the given sources by index.

    The returned `AnswerWithCitations` has only the citations the model
    actually used; out-of-range or hallucinated indices are dropped.

    Raises
    ------
    ValueError
        If `question` is empty or `sources` is empty.
    """
    if not question.strip():
        raise ValueError("question must be non-empty")
    if not sources:
        raise ValueError("sources must be non-empty")

    llm = llm or get_llm()
    prompt = _PROMPT_TEMPLATE.format(
        question=question.strip(),
        source_block=_format_source_block(sources),
    )
    answer_text = llm.complete(prompt).strip()

    used_indices = _extract_cited_indices(answer_text, len(sources))
    citations = [Citation(index=i, source=sources[i - 1]) for i in used_indices]

    return AnswerWithCitations(
        question=question.strip(),
        answer=answer_text,
        citations=citations,
    )
