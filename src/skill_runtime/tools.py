"""OpenEcho Skill Tools — atom 6.3.

Registry of tools available to skills: memory_read, todoist_api, ask_user, scheduler_set.
Each tool is a callable that returns a result or raises an error.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Raised when a tool call fails."""


# Tool type: async callable that takes kwargs and returns a result
ToolFunc = Callable[..., Awaitable[Any]]


class ToolRegistry:
    """Registry of available tools for skills."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolFunc] = {}

    def register(self, name: str, func: ToolFunc) -> None:
        """Register a tool by name."""
        self._tools[name] = func

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    async def call(self, name: str, **kwargs: Any) -> Any:
        """Call a registered tool. Returns result or raises ToolError."""
        if name not in self._tools:
            raise ToolError(f"Unknown tool: {name}")
        try:
            return await self._tools[name](**kwargs)
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Tool '{name}' failed: {e}") from e


# --- Placeholder tool implementations ---

async def ask_user(text: str, **kwargs: Any) -> dict[str, Any]:
    """Ask user a question (returns signal, not actual answer)."""
    return {"type": "question", "text": text}


async def memory_search(query: str, **kwargs: Any) -> dict[str, Any]:
    """Search memory (placeholder)."""
    return {"results": [], "query": query}


async def memory_get(id: str, **kwargs: Any) -> dict[str, Any]:
    """Get memory entry by ID (placeholder)."""
    return {"id": id, "full_text": "", "tokens": 0}


async def scheduler_set(schedule: str, intent: str, **kwargs: Any) -> dict[str, Any]:
    """Set a scheduled task (placeholder)."""
    return {"status": "created", "schedule": schedule, "intent": intent}


def create_default_registry() -> ToolRegistry:
    """Create a registry with all default tools."""
    reg = ToolRegistry()
    reg.register("ask_user", ask_user)
    reg.register("memory_search", memory_search)
    reg.register("memory_get", memory_get)
    reg.register("scheduler_set", scheduler_set)
    return reg
