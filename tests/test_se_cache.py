"""Run the same persistence contract on both cache implementations."""

import pytest

from researcher.cache import JsonCache, MemoryCache


@pytest.fixture(params=["memory", "json"])
def cache(request, tmp_path):
    return MemoryCache(60) if request.param == "memory" else JsonCache(tmp_path, 60, "test")


def test_miss(cache):
    assert cache.get("wiki", "q") is None


def test_roundtrip(cache, sample_sources):
    cache.put("wiki", "Q?", sample_sources)
    assert cache.get("wiki", "q") == sample_sources
    assert cache.get("web", "q") is None


def test_expiry(cache, sample_sources, monkeypatch):
    monkeypatch.setattr("researcher.cache.time.time", lambda: 100)
    cache.put("wiki", "q", sample_sources)
    monkeypatch.setattr("researcher.cache.time.time", lambda: 160)
    assert cache.get("wiki", "q") is None


def test_corrupt(tmp_path):
    cache = JsonCache(tmp_path, 60, "test")
    cache.path("wiki", "q").write_text("broken")
    assert cache.get("wiki", "q") is None


def test_namespace_and_traversal(tmp_path):
    a, b = JsonCache(tmp_path, 1, "live"), JsonCache(tmp_path, 1, "offline")
    assert a.path("wiki", "../../secret").parent == tmp_path
    assert a.path("wiki", "q") != b.path("wiki", "q")


def test_io_failure(tmp_path, sample_sources):
    root = tmp_path / "file"
    root.write_text("not a directory")
    cache = JsonCache(root, 60, "test")
    cache.put("wiki", "q", sample_sources)
    assert cache.get("wiki", "q") is None
