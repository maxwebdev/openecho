"""OpenEcho Pending Confirmation — atoms 4.1, 4.2, 4.3.

Manages intents waiting for user confirmation before being queued.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PendingIntent:
    """Intent awaiting user confirmation."""
    text: str
    skill_hint: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class PendingManager:
    """Per-user pending intent manager."""

    def __init__(self) -> None:
        self._pending: dict[str, list[PendingIntent]] = {}

    def add(self, user_id: str, intent: PendingIntent) -> str:
        """Add intent to pending list. Returns confirmation message for user."""
        if user_id not in self._pending:
            self._pending[user_id] = []
        self._pending[user_id].append(intent)
        skill_name = intent.skill_hint or "неизвестный скилл"
        return f"Запустить «{intent.text}» ({skill_name})? (да/нет)"

    def confirm(self, user_id: str) -> PendingIntent | None:
        """Confirm first pending intent. Returns it for queueing, or None."""
        items = self._pending.get(user_id, [])
        if not items:
            return None
        intent = items.pop(0)
        if not items:
            del self._pending[user_id]
        return intent

    def reject(self, user_id: str) -> PendingIntent | None:
        """Reject first pending intent. Returns removed intent, or None."""
        items = self._pending.get(user_id, [])
        if not items:
            return None
        intent = items.pop(0)
        if not items:
            del self._pending[user_id]
        return intent

    def has_pending(self, user_id: str) -> bool:
        return bool(self._pending.get(user_id))

    def peek(self, user_id: str) -> list[PendingIntent]:
        return list(self._pending.get(user_id, []))

    def clear(self, user_id: str) -> None:
        self._pending.pop(user_id, None)
