"""Tests for Memory API — atom 7.4."""
import pytest
from unittest.mock import MagicMock

from src.memory.reader import MemorySearchResult, MemoryFullResult


@pytest.mark.unit
class TestMemoryAPI:
    @pytest.mark.asyncio
    async def test_memory_search(self):
        from src.memory.api import MemoryAPI
        mock_reader = MagicMock()
        mock_reader.search.return_value = [
            MemorySearchResult(id="m1", summary="Обида", skill="психолог", timestamp="2024-03-15"),
        ]
        api = MemoryAPI(mock_reader)
        result = await api.memory_search("обида", skill="психолог")
        assert len(result["results"]) == 1
        assert result["results"][0]["id"] == "m1"

    @pytest.mark.asyncio
    async def test_memory_get(self):
        from src.memory.api import MemoryAPI
        mock_reader = MagicMock()
        mock_reader.get_full.return_value = MemoryFullResult(id="m1", full_text="Полный текст", tokens=2)
        api = MemoryAPI(mock_reader)
        result = await api.memory_get("m1")
        assert result["id"] == "m1"
        assert result["full_text"] == "Полный текст"

    @pytest.mark.asyncio
    async def test_memory_get_not_found(self):
        from src.memory.api import MemoryAPI
        mock_reader = MagicMock()
        mock_reader.get_full.return_value = None
        api = MemoryAPI(mock_reader)
        result = await api.memory_get("missing")
        assert result["full_text"] == ""
        assert result["tokens"] == 0
