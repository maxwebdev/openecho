"""OpenEcho Gateway State Reader — atom 2.7.

Reads session state from Redis at the start of each message processing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.session import SessionState


@dataclass
class GatewayContext:
    """Session context for gateway decision-making."""
    user_id: str
    active_skill: str
    status: str  # idle, busy, waiting_answer
    pending_intents: list[str]

    @property
    def has_active_skill(self) -> bool:
        return bool(self.active_skill)

    @property
    def is_idle(self) -> bool:
        return self.status == "idle"


async def read_state(session: SessionState, user_id: str) -> GatewayContext:
    """Read session state and return gateway context."""
    state = await session.get(user_id)
    return GatewayContext(
        user_id=user_id,
        active_skill=state.get("active_skill", ""),
        status=state.get("status", "idle"),
        pending_intents=state.get("pending_intents", []),
    )
