"""Tests for src/gateway/state_reader.py — atom 2.7."""
import pytest
from unittest.mock import AsyncMock

from src.gateway.state_reader import read_state, GatewayContext


@pytest.mark.unit
@pytest.mark.asyncio
async def test_read_state_idle():
    session = AsyncMock()
    session.get = AsyncMock(return_value={
        "active_skill": "",
        "status": "idle",
        "pending_intents": [],
    })
    ctx = await read_state(session, "user1")
    assert ctx.is_idle
    assert not ctx.has_active_skill
    assert ctx.pending_intents == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_read_state_busy():
    session = AsyncMock()
    session.get = AsyncMock(return_value={
        "active_skill": "task-manager",
        "status": "busy",
        "pending_intents": ["do stuff"],
    })
    ctx = await read_state(session, "user1")
    assert not ctx.is_idle
    assert ctx.has_active_skill
    assert ctx.active_skill == "task-manager"
    assert len(ctx.pending_intents) == 1
