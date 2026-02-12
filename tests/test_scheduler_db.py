"""Tests for Scheduler DB — atom 9.1."""
import pytest

from src.scheduler.db import SchedulerDB, Schedule


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_sched.db"
    sdb = SchedulerDB(db_path)
    sdb.connect()
    yield sdb
    sdb.close()


@pytest.mark.unit
class TestSchedulerDB:
    def test_add_and_get_all(self, db):
        s = Schedule(id=None, skill_id="task-manager", cron_expr="0 8 * * *",
                     intent="Показать задачи на сегодня", silent=False)
        sid = db.add(s)
        assert sid > 0
        all_s = db.get_all()
        assert len(all_s) == 1
        assert all_s[0].skill_id == "task-manager"
        assert all_s[0].cron_expr == "0 8 * * *"

    def test_get_by_skill(self, db):
        db.add(Schedule(id=None, skill_id="task-manager", cron_expr="0 8 * * *", intent="утро"))
        db.add(Schedule(id=None, skill_id="психолог", cron_expr="0 21 * * *", intent="рефлексия"))
        results = db.get_by_skill("task-manager")
        assert len(results) == 1
        assert results[0].intent == "утро"

    def test_delete(self, db):
        sid = db.add(Schedule(id=None, skill_id="test", cron_expr="* * * * *", intent="test"))
        db.delete(sid)
        assert len(db.get_all()) == 0

    def test_delete_by_skill_and_source(self, db):
        db.add(Schedule(id=None, skill_id="s1", cron_expr="0 8 * * *", intent="a", source="config"))
        db.add(Schedule(id=None, skill_id="s1", cron_expr="0 12 * * *", intent="b", source="user"))
        db.delete_by_skill_and_source("s1", "config")
        remaining = db.get_all()
        assert len(remaining) == 1
        assert remaining[0].source == "user"

    def test_enabled_filter(self, db):
        db.add(Schedule(id=None, skill_id="s1", cron_expr="* * * * *", intent="on", enabled=True))
        db.add(Schedule(id=None, skill_id="s2", cron_expr="* * * * *", intent="off", enabled=False))
        enabled = db.get_all(enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].intent == "on"
        all_s = db.get_all(enabled_only=False)
        assert len(all_s) == 2
