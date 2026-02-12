"""Tests for src/session.py — atom 0.3 (unit, mocked Redis)."""
import json
import pytest
from unittest.mock import AsyncMock

from src.session import SessionState


def _make_session():
    s = SessionState.__new__(SessionState)
    s._redis = AsyncMock()
    return s


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_returns_default_when_empty():
    s = _make_session()
    s._redis.hgetall = AsyncMock(return_value={})

    result = await s.get("user1")
    assert result["active_skill"] == ""
    assert result["status"] == "idle"
    assert result["pending_intents"] == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_writes_to_redis():
    s = _make_session()
    s._redis.delete = AsyncMock()
    s._redis.hset = AsyncMock()

    state = {"active_skill": "task-manager", "status": "busy", "pending_intents": ["a", "b"]}
    await s.set("user1", state)

    s._redis.delete.assert_called_once_with("session:user1")
    s._redis.hset.assert_called_once()
    call_kwargs = s._redis.hset.call_args
    mapping = call_kwargs.kwargs.get("mapping") or call_kwargs[1].get("mapping")
    assert mapping["active_skill"] == "task-manager"
    assert json.loads(mapping["pending_intents"]) == ["a", "b"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_clear_deletes_key():
    s = _make_session()
    s._redis.delete = AsyncMock()

    await s.clear("user1")
    s._redis.delete.assert_called_once_with("session:user1")
