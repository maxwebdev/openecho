"""OpenEcho Intent Queue — atoms 3.1, 3.2, 3.3.

Priority queue for parsed intents. Lower priority number = higher priority.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class QueuedIntent:
    """Intent in the priority queue."""
    priority: int
    text: str = field(compare=False)
    skill_hint: str = field(compare=False, default="")
    metadata: dict[str, Any] = field(compare=False, default_factory=dict)
    _seq: int = field(compare=True, default=0)  # FIFO tiebreaker


class IntentQueue:
    """Priority queue for intents. Thread-safe not required (single async loop)."""

    def __init__(self) -> None:
        self._heap: list[QueuedIntent] = []
        self._seq = 0

    def add(self, text: str, priority: int = 5, skill_hint: str = "", **meta: Any) -> None:
        """Add intent to queue with priority (1=high, 10=low)."""
        item = QueuedIntent(
            priority=priority,
            text=text,
            skill_hint=skill_hint,
            metadata=meta,
            _seq=self._seq,
        )
        self._seq += 1
        heapq.heappush(self._heap, item)

    def pop(self) -> QueuedIntent | None:
        """Remove and return highest-priority intent, or None if empty."""
        if not self._heap:
            return None
        return heapq.heappop(self._heap)

    def peek(self) -> list[QueuedIntent]:
        """View all queued intents (sorted by priority)."""
        return sorted(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)

    def clear(self) -> None:
        self._heap.clear()
        self._seq = 0
