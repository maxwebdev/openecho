"""OpenEcho Gateway Level 0 — Buffer — atom 2.1.

Accumulates forwarded messages / photos without intent.
When an intent arrives, attaches buffered items.
Timer (60s) asks user "what to do with these?" if no intent follows.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BufferItem:
    """Single buffered message."""
    type: str  # "forwarded", "photo", etc.
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MessageBuffer:
    """Per-user message buffer with timeout."""

    TIMEOUT_SEC = 60.0

    def __init__(self) -> None:
        self._buffers: dict[str, list[BufferItem]] = {}
        self._timers: dict[str, asyncio.TimerHandle | asyncio.Task | None] = {}
        self._timeout_callback: Any = None

    def set_timeout_callback(self, callback: Any) -> None:
        """Set callback(user_id) called when buffer times out."""
        self._timeout_callback = callback

    def add(self, user_id: str, item: BufferItem) -> None:
        """Add an item to user's buffer."""
        if user_id not in self._buffers:
            self._buffers[user_id] = []
        self._buffers[user_id].append(item)

    def has_items(self, user_id: str) -> bool:
        """Check if user has buffered items."""
        return bool(self._buffers.get(user_id))

    def collect(self, user_id: str) -> list[BufferItem]:
        """Collect and clear all buffered items for user."""
        items = self._buffers.pop(user_id, [])
        self._cancel_timer(user_id)
        return items

    def peek(self, user_id: str) -> list[BufferItem]:
        """View buffered items without clearing."""
        return list(self._buffers.get(user_id, []))

    def clear(self, user_id: str) -> None:
        """Discard buffer for user."""
        self._buffers.pop(user_id, None)
        self._cancel_timer(user_id)

    def start_timer(self, user_id: str, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """Start timeout timer for user's buffer."""
        self._cancel_timer(user_id)

        async def _fire():
            await asyncio.sleep(self.TIMEOUT_SEC)
            if self._timeout_callback and self.has_items(user_id):
                await self._timeout_callback(user_id)

        _loop = loop or asyncio.get_event_loop()
        self._timers[user_id] = _loop.create_task(_fire())

    def _cancel_timer(self, user_id: str) -> None:
        timer = self._timers.pop(user_id, None)
        if timer and isinstance(timer, asyncio.Task):
            timer.cancel()
