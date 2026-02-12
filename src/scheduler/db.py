"""OpenEcho Scheduler DB — atom 9.1.

SQLite storage for schedules (CRUD).
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Schedule:
    id: int | None
    skill_id: str
    cron_expr: str
    intent: str
    silent: bool = False
    source: str = "config"  # "config" or "user"
    enabled: bool = True


class SchedulerDB:
    def __init__(self, db_path: str | Path = "scheduler.db") -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                cron_expr TEXT NOT NULL,
                intent TEXT NOT NULL,
                silent INTEGER DEFAULT 0,
                source TEXT DEFAULT 'config',
                enabled INTEGER DEFAULT 1
            )
        """)
        self._conn.commit()

    def add(self, schedule: Schedule) -> int:
        assert self._conn
        cur = self._conn.execute(
            "INSERT INTO schedules (skill_id, cron_expr, intent, silent, source, enabled) VALUES (?,?,?,?,?,?)",
            (schedule.skill_id, schedule.cron_expr, schedule.intent,
             int(schedule.silent), schedule.source, int(schedule.enabled)),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_all(self, enabled_only: bool = True) -> list[Schedule]:
        assert self._conn
        query = "SELECT * FROM schedules"
        if enabled_only:
            query += " WHERE enabled = 1"
        rows = self._conn.execute(query).fetchall()
        return [self._row_to_schedule(r) for r in rows]

    def get_by_skill(self, skill_id: str) -> list[Schedule]:
        assert self._conn
        rows = self._conn.execute("SELECT * FROM schedules WHERE skill_id = ?", (skill_id,)).fetchall()
        return [self._row_to_schedule(r) for r in rows]

    def delete(self, schedule_id: int) -> None:
        assert self._conn
        self._conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
        self._conn.commit()

    def delete_by_skill_and_source(self, skill_id: str, source: str = "config") -> None:
        assert self._conn
        self._conn.execute("DELETE FROM schedules WHERE skill_id = ? AND source = ?", (skill_id, source))
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @staticmethod
    def _row_to_schedule(row: sqlite3.Row) -> Schedule:
        return Schedule(
            id=row["id"], skill_id=row["skill_id"], cron_expr=row["cron_expr"],
            intent=row["intent"], silent=bool(row["silent"]),
            source=row["source"], enabled=bool(row["enabled"]),
        )
