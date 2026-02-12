"""OpenEcho Scheduler Config Scanner — atom 9.2.

Reads skills/*/config.yaml -> syncs cron schedules with DB.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.config_loader import load_skills
from src.scheduler.db import SchedulerDB, Schedule


class ConfigScanner:
    def __init__(self, scheduler_db: SchedulerDB, skills_dir: str | Path = "skills") -> None:
        self._db = scheduler_db
        self._skills_dir = Path(skills_dir)
        self._checksums: dict[str, str] = {}

    def scan(self) -> int:
        """Scan config files and sync schedules. Returns number of changes."""
        skills = load_skills(self._skills_dir)
        changes = 0

        for skill_id, config in skills.items():
            config_path = self._skills_dir / skill_id / "config.yaml"
            checksum = self._file_checksum(config_path)

            if self._checksums.get(skill_id) == checksum:
                continue  # unchanged

            self._checksums[skill_id] = checksum
            self._db.delete_by_skill_and_source(skill_id, "config")

            for cron_entry in config.cron:
                self._db.add(Schedule(
                    id=None,
                    skill_id=skill_id,
                    cron_expr=cron_entry.get("schedule", ""),
                    intent=cron_entry.get("intent", ""),
                    silent=cron_entry.get("silent", False),
                    source="config",
                ))
                changes += 1

        return changes

    @staticmethod
    def _file_checksum(path: Path) -> str:
        if not path.exists():
            return ""
        return hashlib.md5(path.read_bytes()).hexdigest()
