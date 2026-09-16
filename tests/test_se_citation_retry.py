"""Offline regression checks for rejected model output."""
from unittest.mock import AsyncMock

import pytest

from ai.providers.base import ProviderError
from ai.schemas import AnswerWithCitations
from researcher.config import Settings
from researcher.service import AIService


@pytest.mark.asyncio
async def test_uncited_output_regenerated(sample_sources):
    service = AIService(Settings(attempts=3, backoff=0), offline=True)
    invalid = AnswerWithCitations(question="q", answer="Supported [1]. Uncited claim.", citations=[])
    valid = AnswerWithCitations(question="q", answer="Supported [1].", citations=[])
    service._worker = AsyncMock(side_effect=[invalid.model_dump_json().encode(), valid.model_dump_json().encode()])
    result = await service.synthesize("q", sample_sources)
    assert result.answer == "Supported [1]."
    assert service._worker.await_count == 2
    assert result.citations[0].source == sample_sources[0]


@pytest.mark.asyncio
async def test_invalid_output_stops_at_attempt_limit(sample_sources):
    service = AIService(Settings(attempts=2, backoff=0), offline=True)
    invalid = AnswerWithCitations(question="q", answer="Uncited claim.", citations=[])
    service._worker = AsyncMock(return_value=invalid.model_dump_json().encode())
    with pytest.raises(ProviderError, match="invalid citations"):
        await service.synthesize("q", sample_sources)
    assert service._worker.await_count == 2
