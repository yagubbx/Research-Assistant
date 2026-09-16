"""TTL repositories: interchangeable memory and atomic filesystem storage."""

import hashlib
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import ValidationError

from ai.schemas import Source
from researcher.models import CacheEntry
from researcher.validation import canonical_query

log = logging.getLogger(__name__)


class Cache(ABC):
    """Persistence contract composed into the orchestrator."""

    @abstractmethod
    def get(self, source: str, query: str) -> list[Source] | None:
        """Return unexpired evidence or a cache miss."""
        raise NotImplementedError

    @abstractmethod
    def put(self, source: str, query: str, sources: list[Source]) -> None:
        """Persist evidence with the configured TTL."""
        raise NotImplementedError


class MemoryCache(Cache):
    """An isolated cache for tests and short-lived applications."""

    def __init__(self, ttl: float = 3600) -> None:
        self.ttl = ttl
        self.entries: dict[tuple[str, str], CacheEntry] = {}

    def get(self, source: str, query: str) -> list[Source] | None:
        entry = self.entries.get((source, canonical_query(query)))
        return list(entry.sources) if entry and entry.expires_at > time.time() else None

    def put(self, source: str, query: str, sources: list[Source]) -> None:
        self.entries[source, canonical_query(query)] = CacheEntry(
            expires_at=time.time() + self.ttl, sources=sources
        )


class JsonCache(Cache):
    """One atomic JSON record per namespace/source/query, without a DB server."""

    def __init__(self, root: Path, ttl: float, namespace: str) -> None:
        self.root, self.ttl, self.namespace = root, ttl, namespace

    def path(self, source: str, query: str) -> Path:
        """Hash keys so questions never become filenames or path traversal."""
        key = f"{self.namespace}\0{source}\0{canonical_query(query)}"
        return self.root / (hashlib.sha256(key.encode()).hexdigest() + ".json")

    def get(self, source: str, query: str) -> list[Source] | None:
        try:
            path = self.path(source, query)
            if path.stat().st_size > 1_000_000:
                return None
            entry = CacheEntry.model_validate_json(path.read_text(encoding="utf-8"))
            return entry.sources if entry.expires_at > time.time() else None
        except FileNotFoundError:
            return None
        except (OSError, ValueError, ValidationError):
            log.warning("cache_read_failed source=%s", source)
            return None

    def put(self, source: str, query: str, sources: list[Source]) -> None:
        temp = self.path(source, query).with_suffix(f".{uuid.uuid4().hex}.tmp")
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            entry = CacheEntry(expires_at=time.time() + self.ttl, sources=sources)
            temp.write_text(entry.model_dump_json(), encoding="utf-8")
            os.replace(temp, self.path(source, query))
        except OSError:
            log.warning("cache_write_failed source=%s", source)
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                log.warning("cache_temp_cleanup_failed")
