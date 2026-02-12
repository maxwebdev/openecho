"""OpenEcho Scheduler Timer — atom 9.3.

Checks DB for due schedules and fires events.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from croniter import croniter

from src.scheduler.db import SchedulerDB, Schedule


def get_due_schedules(db: SchedulerDB, now: datetime | None = None) -> list[Schedule]:
    """Return schedules that are due at *now*."""
    now = now or datetime.now()
    schedules = db.get_all(enabled_only=True)
    due = []
    for s in schedules:
        try:
            cron = croniter(s.cron_expr, now)
            prev = cron.get_prev(datetime)
            # If previous trigger was within the last 5 minutes, it is due
            diff = (now - prev).total_seconds()
            if 0 <= diff < 300:  # 5 min window
                due.append(s)
        except Exception:
            continue
    return due
