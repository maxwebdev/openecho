"""OpenEcho Memory Reader — atom 7.3.

Two-step read: search index for summaries, then get full text by ID.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.memory.index import MemoryIndex
from src.memory.vectors import MemoryVectors


@dataclass
class MemorySearchResult:
    id: str
    summary: str
    skill: str
    timestamp: str


@dataclass
class MemoryFullResult:
    id: str
    full_text: str
    tokens: int


class MemoryReader:
    def __init__(self, index: MemoryIndex, vectors: MemoryVectors) -> None:
        self._index = index
        self._vectors = vectors

    def search(self, query: str, skill: str = "", limit: int = 10) -> list[MemorySearchResult]:
        rows = self._index.search(query, skill=skill, limit=limit)
        return [
            MemorySearchResult(
                id=r["id"], summary=r["summary"],
                skill=r["skill"], timestamp=r.get("timestamp", ""),
            )
            for r in rows
        ]

    def get_full(self, card_id: str) -> MemoryFullResult | None:
        doc = self._vectors.get(card_id)
        if not doc:
            return None
        text = doc.get("text", "")
        return MemoryFullResult(id=card_id, full_text=text, tokens=len(text.split()))
