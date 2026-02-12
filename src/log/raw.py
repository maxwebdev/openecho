"""OpenEcho Raw Session Log — atom 8.2.

Writes filtered messages to a session log file with timestamps.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RawSessionLog:
    """Writes session messages to a JSONL file."""

    def __init__(self, log_dir: str | Path = "logs/sessions") -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        return self._log_dir / f"{session_id}.jsonl"

    def write(self, session_id: str, role: str, text: str, **extra: Any) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "text": text,
            **extra,
        }
        with open(self._session_file(session_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read(self, session_id: str) -> list[dict[str, Any]]:
        path = self._session_file(session_id)
        if not path.exists():
            return []
        entries = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries
