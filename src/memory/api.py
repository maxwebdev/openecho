"""OpenEcho Memory API — atom 7.4.

Skill-facing tools: memory_search and memory_get.
"""
from __future__ import annotations

from typing import Any

from src.memory.reader import MemoryReader


class MemoryAPI:
    def __init__(self, reader: MemoryReader) -> None:
        self._reader = reader

    async def memory_search(self, query: str, skill: str = "", limit: int = 10) -> dict[str, Any]:
        results = self._reader.search(query, skill=skill, limit=limit)
        return {
            "results": [
                {"id": r.id, "summary": r.summary, "skill": r.skill, "timestamp": r.timestamp}
                for r in results
            ]
        }

    async def memory_get(self, id: str) -> dict[str, Any]:
        result = self._reader.get_full(id)
        if not result:
            return {"id": id, "full_text": "", "tokens": 0}
        return {"id": result.id, "full_text": result.full_text, "tokens": result.tokens}
