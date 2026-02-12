"""Tests for src/logger.py — atom 0.4."""
import json
import os
import tempfile
import pytest

from src.logger import log_event


@pytest.mark.unit
def test_log_event_writes_valid_json(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_DIR", str(tmp_path))

    event = log_event(
        "gateway.level2",
        "parse_intents",
        input_data="test message",
        output_data={"intents": [{"text": "do stuff", "skill": "task-manager"}]},
    )

    # Check returned dict
    assert event["component"] == "gateway.level2"
    assert event["action"] == "parse_intents"
    assert "timestamp" in event

    # Check file was written
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1

    with open(files[0], encoding="utf-8") as f:
        line = f.readline()
        parsed = json.loads(line)
        assert parsed["component"] == "gateway.level2"
        assert parsed["action"] == "parse_intents"
        assert parsed["input"] == "test message"


@pytest.mark.unit
def test_log_event_with_llm_call(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_DIR", str(tmp_path))

    event = log_event(
        "skill.task-manager",
        "llm_call",
        llm_call={"model": "haiku", "prompt_tokens": 280, "completion_tokens": 60, "duration_ms": 800},
    )

    assert event["llm_call"]["model"] == "haiku"

    files = list(tmp_path.glob("*.jsonl"))
    with open(files[0], encoding="utf-8") as f:
        parsed = json.loads(f.readline())
        assert parsed["llm_call"]["prompt_tokens"] == 280


@pytest.mark.unit
def test_log_event_minimal(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_DIR", str(tmp_path))

    event = log_event("test", "ping")

    assert "input" not in event
    assert "output" not in event
    assert "llm_call" not in event
