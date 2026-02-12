"""Tests for src/skill_runtime/llm.py — atom 6.2."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.skill_runtime.llm import call_llm, LLMError, graceful_llm_error


@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_llm_no_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        await call_llm("system", "user")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_llm_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "content": [{"type": "text", "text": "Hello from Haiku"}]
    })

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await call_llm("You are a test", "Say hello")
        assert result == "Hello from Haiku"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_llm_retry(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    call_count = 0

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("temporary error")
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value={"content": [{"type": "text", "text": "ok"}]})
        return resp

    mock_client.post = mock_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await call_llm("sys", "usr", max_retries=3)
            assert result == "ok"
            assert call_count == 3


@pytest.mark.unit
def test_graceful_llm_error():
    msg = graceful_llm_error()
    assert isinstance(msg, str)
    assert len(msg) > 10
