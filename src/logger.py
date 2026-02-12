"""OpenEcho Logger — atom 0.4.

Structured logging with structlog to JSONL files.
Format matches Debug-mode.md: timestamp, component, action, input, output, llm_call.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog


def _get_log_dir() -> Path:
    base = Path(os.getenv("LOG_DIR", "logs/events"))
    base.mkdir(parents=True, exist_ok=True)
    return base


def _today_file() -> Path:
    return _get_log_dir() / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"


def setup_logging() -> None:
    """Configure structlog for the whole app (call once at startup)."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def log_event(
    component: str,
    action: str,
    *,
    input_data: Any = None,
    output_data: Any = None,
    llm_call: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a structured event to today JSONL log file.

    Returns the event dict for testing convenience.
    """
    event: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "action": action,
    }
    if input_data is not None:
        event["input"] = input_data
    if output_data is not None:
        event["output"] = output_data
    if llm_call is not None:
        event["llm_call"] = llm_call

    line = json.dumps(event, ensure_ascii=False)
    with open(_today_file(), "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return event
