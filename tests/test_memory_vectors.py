"""Tests for Memory Vectors — atom 7.2."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestMemoryVectors:
    def test_add_and_get(self):
        from src.memory.vectors import MemoryVectors
        mv = MemoryVectors("test_col")
        mock_col = MagicMock()
        mock_col.get.return_value = {
            "ids": ["doc1"],
            "documents": ["full text here"],
            "metadatas": [{"skill": "психолог"}],
        }
        mv._collection = mock_col
        mv.add("doc1", "full text here", {"skill": "психолог"})
        mock_col.upsert.assert_called_once_with(
            ids=["doc1"], documents=["full text here"], metadatas=[{"skill": "психолог"}],
        )
        result = mv.get("doc1")
        assert result["id"] == "doc1"
        assert result["text"] == "full text here"

    def test_get_nonexistent(self):
        from src.memory.vectors import MemoryVectors
        mv = MemoryVectors("test_col")
        mock_col = MagicMock()
        mock_col.get.return_value = {"ids": [], "documents": [], "metadatas": []}
        mv._collection = mock_col
        result = mv.get("nonexistent")
        assert result is None

    def test_search(self):
        from src.memory.vectors import MemoryVectors
        mv = MemoryVectors("test_col")
        mock_col = MagicMock()
        mock_col.query.return_value = {
            "ids": [["d1", "d2"]],
            "documents": [["text one", "text two"]],
            "metadatas": [[{"skill": "a"}, {"skill": "b"}]],
            "distances": [[0.1, 0.5]],
        }
        mv._collection = mock_col
        results = mv.search("query", n_results=2)
        assert len(results) == 2
        assert results[0]["id"] == "d1"
        assert results[0]["distance"] == 0.1

    def test_search_with_where(self):
        from src.memory.vectors import MemoryVectors
        mv = MemoryVectors("test_col")
        mock_col = MagicMock()
        mock_col.query.return_value = {
            "ids": [["d1"]], "documents": [["text"]], "metadatas": [[{}]], "distances": [[0.2]],
        }
        mv._collection = mock_col
        mv.search("query", where={"skill": "психолог"})
        call_kwargs = mock_col.query.call_args[1]
        assert call_kwargs["where"] == {"skill": "психолог"}
