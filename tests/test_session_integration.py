"""Integration tests for src/session.py — atom 0.3 (real Redis)."""
import pytest

from src.session import SessionState


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_crud_real_redis():
    s = SessionState("redis://localhost:6379/0")
    user = "test_user_integration"

    # Clean start
    await s.clear(user)

    # Default state
    state = await s.get(user)
    assert state["status"] == "idle"

    # Set
    await s.set(user, {"active_skill": "psychologist", "status": "busy", "pending_intents": ["x"]})
    state = await s.get(user)
    assert state["active_skill"] == "psychologist"
    assert state["status"] == "busy"
    assert state["pending_intents"] == ["x"]

    # Update
    await s.update(user, status="idle")
    state = await s.get(user)
    assert state["status"] == "idle"
    assert state["active_skill"] == "psychologist"  # unchanged

    # Cleanup
    await s.clear(user)
    await s.close()
