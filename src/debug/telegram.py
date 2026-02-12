"""OpenEcho Debug Telegram — atom 10.1.

/debug on/off command, appends debug block under bot responses.
"""
from __future__ import annotations

from typing import Any


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
        """Format debug events into a Telegram-friendly block."""
        if not events:
            return ""
        lines = ["──── debug ────"]
        for ev in events:
            component = ev.get("component", "?")
            action = ev.get("action", "?")
            line = f"{component}: {action}"
            if "llm_call" in ev:
                llm = ev["llm_call"]
                line += f" ({llm.get('model', '?')}, {llm.get('prompt_tokens', 0)}+{llm.get('completion_tokens', 0)} tok)"
            lines.append(line)
        lines.append("───────────────")
        return "\n".join(lines)
