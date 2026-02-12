"""Tests for Memory Index — atom 7.1."""
import pytest
import tempfile
import os

from src.memory.index import MemoryIndex, IndexCard


@pytest.fixture
def index(tmp_path):
    db_path = tmp_path / "test_memory.db"
    idx = MemoryIndex(db_path)
    idx.connect()
    yield idx
    idx.close()


@pytest.mark.unit
class TestMemoryIndex:
    def test_add_and_get(self, index):
        card = IndexCard(
            id="mem_001", skill="психолог", intent="рефлексия",
            summary="Обида на маму из детства",
            tags="семья обида", timestamp="2024-03-15",
        )
        index.add(card)
        result = index.get("mem_001")
        assert result is not None
        assert result["id"] == "mem_001"
        assert result["skill"] == "психолог"
        assert result["summary"] == "Обида на маму из детства"

    def test_get_nonexistent(self, index):
        result = index.get("nonexistent")
        assert result is None

    def test_search_fts(self, index):
        index.add(IndexCard(id="m1", skill="психолог", intent="", summary="Обида на маму из детства", tags="семья"))
        index.add(IndexCard(id="m2", skill="задачник", intent="", summary="Купить молоко завтра", tags="задачи"))
        index.add(IndexCard(id="m3", skill="психолог", intent="", summary="Конфликт с мамой по телефону", tags="семья"))
        results = index.search("мам*")
        ids = [r["id"] for r in results]
        assert "m1" in ids
        assert "m3" in ids
        assert "m2" not in ids

    def test_search_with_skill_filter(self, index):
        index.add(IndexCard(id="m1", skill="психолог", intent="", summary="Обида на маму", tags="семья"))
        index.add(IndexCard(id="m2", skill="задачник", intent="", summary="Позвонить маме", tags="задачи"))
        results = index.search("маму", skill="психолог")
        assert len(results) == 1
        assert results[0]["id"] == "m1"

    def test_upsert_replace(self, index):
        index.add(IndexCard(id="m1", skill="психолог", intent="", summary="Первая версия"))
        index.add(IndexCard(id="m1", skill="психолог", intent="", summary="Обновлённая версия"))
        result = index.get("m1")
        assert result["summary"] == "Обновлённая версия"
