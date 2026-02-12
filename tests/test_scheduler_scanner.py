"""Tests for Scheduler Config Scanner — atom 9.2."""
import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.scheduler.db import SchedulerDB, Schedule
from src.scheduler.scanner import ConfigScanner


@pytest.fixture
def skills_dir(tmp_path):
    """Create a temporary skills directory with a config."""
    skill_dir = tmp_path / "task-manager"
    skill_dir.mkdir()
    config = {
        "name": "Задачник",
        "type": "executor",
        "description": "Управление задачами",
        "llm": {"provider": "anthropic", "model": "haiku", "max_tokens": 1000, "temperature": 0.3},
        "tools": ["todoist_api"],
        "priority": 2,
        "triggers": ["задача"],
        "cron": [
            {"schedule": "0 8 * * *", "intent": "Показать задачи на сегодня", "silent": False},
        ],
    }
    (skill_dir / "config.yaml").write_text(yaml.dump(config, allow_unicode=True))
    return tmp_path


@pytest.mark.unit
class TestConfigScanner:
    def test_scan_finds_cron(self, skills_dir, tmp_path):
        db = SchedulerDB(tmp_path / "sched.db")
        db.connect()
        scanner = ConfigScanner(db, skills_dir)
        changes = scanner.scan()
        assert changes == 1
        schedules = db.get_all()
        assert len(schedules) == 1
        assert schedules[0].cron_expr == "0 8 * * *"
        db.close()

    def test_scan_checksum_skip(self, skills_dir, tmp_path):
        db = SchedulerDB(tmp_path / "sched.db")
        db.connect()
        scanner = ConfigScanner(db, skills_dir)
        scanner.scan()  # first scan
        changes = scanner.scan()  # second scan — same checksum
        assert changes == 0
        db.close()

    def test_scan_detects_change(self, skills_dir, tmp_path):
        db = SchedulerDB(tmp_path / "sched.db")
        db.connect()
        scanner = ConfigScanner(db, skills_dir)
        scanner.scan()

        # Modify the config
        config_path = skills_dir / "task-manager" / "config.yaml"
        config = yaml.safe_load(config_path.read_text())
        config["cron"].append({"schedule": "0 21 * * *", "intent": "Вечерний обзор", "silent": True})
        config_path.write_text(yaml.dump(config, allow_unicode=True))

        changes = scanner.scan()
        assert changes == 2  # old deleted + 2 new added
        schedules = db.get_all()
        assert len(schedules) == 2
        db.close()
