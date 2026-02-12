"""Tests for Log Indexer — atom 8.3."""
import pytest
import json

from src.log.indexer import chunk_log, index_session


@pytest.mark.unit
class TestLogIndexer:
    def test_chunk_log_small(self):
        messages = [{"text": "hello"}, {"text": "world"}]
        chunks = chunk_log(messages, max_tokens=1000)
        assert len(chunks) == 1
        assert len(chunks[0]) == 2

    def test_chunk_log_split(self):
        # Create a message that is ~1500 tokens (lots of words)
        big_msg = {"text": " ".join(["word"] * 1200)}
        small_msg = {"text": "short"}
        chunks = chunk_log([big_msg, small_msg], max_tokens=1000)
        assert len(chunks) == 2

    def test_chunk_log_empty(self):
        chunks = chunk_log([], max_tokens=1000)
        assert chunks == []

    @pytest.mark.asyncio
    async def test_index_session_basic(self):
        messages = [
            {"role": "user", "text": "Я обиделся на маму"},
            {"role": "bot", "text": "Расскажи подробнее"},
        ]

        async def mock_llm(system, user):
            return json.dumps([
                {"id": "c1", "skill": "психолог", "intent": "рефлексия", "summary": "Обида на маму", "tags": "семья"}
            ])

        cards = await index_session(messages, llm_call=mock_llm, session_id="s1")
        assert len(cards) == 1
        assert cards[0]["summary"] == "Обида на маму"

    @pytest.mark.asyncio
    async def test_index_session_no_llm(self):
        cards = await index_session([{"text": "hello"}], llm_call=None)
        assert cards == []

    @pytest.mark.asyncio
    async def test_index_session_empty(self):
        async def mock_llm(s, u):
            return "[]"
        cards = await index_session([], llm_call=mock_llm)
        assert cards == []

    @pytest.mark.asyncio
    async def test_index_session_llm_error(self):
        messages = [{"role": "user", "text": "test"}]

        async def broken_llm(system, user):
            raise RuntimeError("LLM down")

        cards = await index_session(messages, llm_call=broken_llm, session_id="s1")
        assert cards == []
