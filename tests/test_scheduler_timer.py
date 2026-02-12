"""Tests for Scheduler Timer — atom 9.3."""
import pytest
from datetime import datetime

from src.scheduler.db import SchedulerDB, Schedule
from src.scheduler.timer import get_due_schedules


@pytest.fixture
def db(tmp_path):
    sdb = SchedulerDB(tmp_path / "timer_test.db")
    sdb.connect()
    yield sdb
    sdb.close()


@pytest.mark.unit
class TestSchedulerTimer:
    def test_due_schedule(self, db):
        db.add(Schedule(id=None, skill_id="task-manager", cron_expr="0 8 * * *", intent="утро"))
        # Simulate checking at 08:02 — within 5 min window
        now = datetime(2025, 2, 12, 8, 2, 0)
        due = get_due_schedules(db, now=now)
        assert len(due) == 1
        assert due[0].intent == "утро"

    def test_not_due(self, db):
        db.add(Schedule(id=None, skill_id="task-manager", cron_expr="0 8 * * *", intent="утро"))
        # Check at 14:00 — not due
        now = datetime(2025, 2, 12, 14, 0, 0)
        due = get_due_schedules(db, now=now)
        assert len(due) == 0

    def test_multiple_due(self, db):
        db.add(Schedule(id=None, skill_id="s1", cron_expr="0 8 * * *", intent="a"))
        db.add(Schedule(id=None, skill_id="s2", cron_expr="0 8 * * *", intent="b"))
        now = datetime(2025, 2, 12, 8, 1, 0)
        due = get_due_schedules(db, now=now)
        assert len(due) == 2

    def test_invalid_cron_skipped(self, db):
        db.add(Schedule(id=None, skill_id="s1", cron_expr="INVALID", intent="bad"))
        db.add(Schedule(id=None, skill_id="s2", cron_expr="0 8 * * *", intent="good"))
        now = datetime(2025, 2, 12, 8, 1, 0)
        due = get_due_schedules(db, now=now)
        assert len(due) == 1
        assert due[0].intent == "good"
