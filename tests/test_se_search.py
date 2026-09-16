"""Search query regression tests; no network."""
import pytest

from researcher.search import topic_query


def test_long_question_keeps_topic():
    assert topic_query("What is photosynthesis and what are its main stages?") == "photosynthesis"


def test_preserves_distinctive_terms():
    assert topic_query("What is CRISPR-Cas9?") == "CRISPR-Cas9"
    assert topic_query("How do transformers work?") == "How do transformers work"


def test_short_topic_unchanged():
    assert topic_query("photosynthesis") == "photosynthesis"


@pytest.mark.asyncio
async def test_web_adapter_uses_bounded_backend(monkeypatch):
    import sys
    from types import SimpleNamespace

    from researcher.search import BoundedWebSearch
    class FakeSearch:
        def __init__(self, timeout):
            assert timeout == 5
        def text(self, query, max_results, backend):
            assert backend == "bing"
            return [{"title": "Evidence", "href": "https://example.org", "body": "Text"}]
    monkeypatch.setitem(sys.modules, "ddgs", SimpleNamespace(DDGS=FakeSearch))
    sources = await BoundedWebSearch().search("topic")
    assert sources[0].origin == "web"


@pytest.mark.asyncio
async def test_web_adapter_redacts_failure(monkeypatch):
    import sys
    from types import SimpleNamespace

    import pytest

    from ai.providers.base import ProviderError
    from researcher.search import BoundedWebSearch
    class BrokenSearch:
        def __init__(self, timeout):
            raise RuntimeError("private provider details")
    monkeypatch.setitem(sys.modules, "ddgs", SimpleNamespace(DDGS=BrokenSearch))
    with pytest.raises(ProviderError, match="backend unavailable"):
        await BoundedWebSearch().search("topic")
