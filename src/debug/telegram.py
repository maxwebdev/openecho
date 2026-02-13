"""OpenEcho Debug Telegram — atom 10.1.

/debug on/off command, appends debug block under bot responses.
Shows full message route through the pipeline.
"""
from __future__ import annotations

from typing import Any


# Icons for each pipeline component
ICONS = {
    "input": "📩",
    "session": "💾",
    "forward": "↩️",
    "gateway": "🧠",
    "queue": "📋",
    "dispatcher": "⚡",
    "skill": "🎯",
    "response": "💬",
    "error": "❌",
}


class DebugManager:
    """Per-user debug mode toggle."""

    def __init__(self) -> None:
        self._enabled: set[str] = set()

    def enable(self, user_id: str) -> None:
        self._enabled.add(user_id)

    def disable(self, user_id: str) -> None:
        self._enabled.discard(user_id)

    def is_enabled(self, user_id: str) -> bool:
        return user_id in self._enabled

    def format_debug_block(self, events: list[dict[str, Any]]) -> str:
        """Format debug events as a visual message route."""
        if not events:
            return ""

        lines: list[str] = []
        route_parts: list[str] = []

        for ev in events:
            step = ev.get("step", "")
            icon = ICONS.get(step, "•")
            label = ev.get("label", "")
            detail = ev.get("detail", "")

            if label:
                route_parts.append(f"{icon}{label}")

            if detail:
                lines.append(f"  {icon} {detail}")

        # Build route line
        route = " → ".join(route_parts) if route_parts else ""

        result = ["─── route ───"]
        if route:
            result.append(route)
        if lines:
            result.extend(lines)
        result.append("─────────────")

        return "\n".join(result)
