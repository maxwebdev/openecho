"""Tests for Memory Reader — atom 7.3."""
import pytest
from unittest.mock import MagicMock


@pytest.mark.unit
class TestMemoryReader:
    def test_search(self):
        from src.memory.reader import MemoryReader
        mock_index = MagicMock()
        mock_index.search.return_value = [
            {"id": "m1", "summary": "Обида на маму", "skill": "психолог", "timestamp": "2024-03-15"},
            {"id": "m2", "summary": "Конфликт по телефону", "skill": "психолог", "timestamp": "2024-06-22"},
        ]
        mock_vectors = MagicMock()
        reader = MemoryReader(mock_index, mock_vectors)
        results = reader.search("маму", skill="психолог")
        assert len(results) == 2
        assert results[0].id == "m1"
        assert results[0].summary == "Обида на маму"

    def test_get_full(self):
        from src.memory.reader import MemoryReader
        mock_index = MagicMock()
        mock_vectors = MagicMock()
        mock_vectors.get.return_value = {
            "id": "m1", "text": "Полный текст сессии рефлексии", "metadata": {},
        }
        reader = MemoryReader(mock_index, mock_vectors)
        result = reader.get_full("m1")
        assert result is not None
        assert result.id == "m1"
        assert result.full_text == "Полный текст сессии рефлексии"
        assert result.tokens > 0

    def test_get_full_not_found(self):
        from src.memory.reader import MemoryReader
        mock_index = MagicMock()
        mock_vectors = MagicMock()
        mock_vectors.get.return_value = None
        reader = MemoryReader(mock_index, mock_vectors)
        result = reader.get_full("nonexistent")
        assert result is None
