"""OpenEcho Memory Index — atom 7.1.

SQLite + FTS5 index for fast keyword search with metadata filtering.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class IndexCard:
    """Memory index card."""
    id: str
    skill: str
    intent: str
    summary: str
    tags: str = ""
    source: str = ""
    timestamp: str = ""


class MemoryIndex:
    """SQLite FTS5 based memory index."""

    def __init__(self, db_path: str | Path = "memory.db") -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        assert self._conn
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY,
                skill TEXT NOT NULL,
                intent TEXT,
                summary TEXT NOT NULL,
                tags TEXT DEFAULT '',
                source TEXT DEFAULT '',
                timestamp TEXT DEFAULT ''
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS cards_fts USING fts5(
                id, summary, tags, content=cards, content_rowid=rowid
            );
            CREATE TRIGGER IF NOT EXISTS cards_ai AFTER INSERT ON cards BEGIN
                INSERT INTO cards_fts(id, summary, tags) VALUES (new.id, new.summary, new.tags);
            END;
        """)

    def add(self, card: IndexCard) -> None:
        assert self._conn
        self._conn.execute(
            "INSERT OR REPLACE INTO cards (id, skill, intent, summary, tags, source, timestamp) VALUES (?,?,?,?,?,?,?)",
            (card.id, card.skill, card.intent, card.summary, card.tags, card.source, card.timestamp),
        )
        self._conn.commit()

    def search(self, query: str, skill: str = "", limit: int = 10) -> list[dict[str, Any]]:
        assert self._conn
        if skill:
            rows = self._conn.execute(
                "SELECT c.* FROM cards c JOIN cards_fts f ON c.id = f.id WHERE cards_fts MATCH ? AND c.skill = ? LIMIT ?",
                (query, skill, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT c.* FROM cards c JOIN cards_fts f ON c.id = f.id WHERE cards_fts MATCH ? LIMIT ?",
                (query, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get(self, card_id: str) -> dict[str, Any] | None:
        assert self._conn
        row = self._conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        return dict(row) if row else None

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
