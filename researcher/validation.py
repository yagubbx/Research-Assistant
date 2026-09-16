"""Pure input and citation validation, including terminal-safe output."""

import re
import unicodedata
from urllib.parse import urlsplit

from ai.schemas import AnswerWithCitations, Citation, Source


def clean_text(text: str) -> str:
    """Strip terminal escape sequences, markup and invisible controls."""
    text = re.sub(r"\x1b\][^\x07]*(?:\x07|\x1b\\)", "", text)
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = re.sub(r"<[^>]*>", "", text)
    return " ".join(
        "".join(c for c in text if not unicodedata.category(c).startswith("C") or c in "\n\t").split()
    )


def validate_question(question: str, limit: int = 2000) -> str:
    """Reject missing, too long or control-only input before any I/O."""
    if len(question) > limit:
        raise ValueError(f"Question must be at most {limit} characters.")
    result = clean_text(question)
    if not result or not any(c.isalnum() for c in result):
        raise ValueError("Question must contain letters or numbers.")
    return result


def canonical_query(question: str) -> str:
    """Ignore case, repeated spaces and a trailing question mark only."""
    return " ".join(unicodedata.normalize("NFKC", question).casefold().split()).rstrip("? ")


def parse_sources(value: str) -> list[str]:
    """Keep user order, rejecting unknown or empty source names."""
    names = [part.strip().lower() for part in value.split(",")]
    if not names or any(name not in {"wiki", "arxiv", "web"} for name in names):
        raise ValueError("Sources must be a comma-separated subset of wiki,arxiv,web.")
    return list(dict.fromkeys(names))


def valid_sources(sources: list[Source]) -> list[Source]:
    """Discard unusable evidence and unsafe reference URLs."""
    result: list[Source] = []
    seen: set[str] = set()
    for source in sources:
        try:
            url = urlsplit(source.url)
            safe = url.scheme in {"https", "http"} and bool(url.hostname) and not url.username
        except ValueError:
            safe = False
        if not safe or any(c.isspace() or unicodedata.category(c).startswith("C") for c in source.url):
            continue
        title, snippet = clean_text(source.title), clean_text(source.snippet)
        if title and snippet and source.url not in seen:
            result.append(
                Source(title=title[:300], snippet=snippet[:4000], url=source.url, origin=source.origin)
            )
            seen.add(source.url)
    return result


def validate_answer(answer: AnswerWithCitations, sources: list[Source], question: str) -> AnswerWithCitations:
    """Remove dangling markers and reject unsupported, uncited sentences.

    This checks citation structure, not whether the evidence entails a claim.
    """
    used: set[int] = set()

    def replace(match: re.Match[str]) -> str:
        indices = sorted({int(i.strip()) for i in match[1].split(",") if 1 <= int(i.strip()) <= len(sources)})
        used.update(indices)
        return "[" + ",".join(map(str, indices)) + "]" if indices else ""

    text = re.sub(r"\[(\d+(?:\s*,\s*\d+)*)\]", replace, clean_text(answer.answer))
    if not text or not used:
        raise ValueError("The model returned no usable cited answer.")
    # Move a citation placed after sentence punctuation before splitting.
    check = re.sub(r"([.!?])\s*(\[[\d,]+\])", r" \2\1", text)
    for sentence in re.split(r"(?<=[.!?])\s+", check):
        if any(c.isalpha() for c in sentence) and not re.search(r"\[[\d,]+\]", sentence):
            raise ValueError("The model returned an uncited sentence; retry the question.")
    return AnswerWithCitations(
        question=question,
        answer=text,
        citations=[Citation(index=i, source=sources[i - 1]) for i in sorted(used)],
    )
