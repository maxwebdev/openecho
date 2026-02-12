"""Tests for Raw Session Log — atom 8.2."""
import pytest
import json

from src.log.raw import RawSessionLog


@pytest.mark.unit
class TestRawSessionLog:
    def test_write_and_read(self, tmp_path):
        log = RawSessionLog(log_dir=tmp_path / "sessions")
        log.write("sess_001", "user", "Создай задачу купить молоко")
        log.write("sess_001", "bot", "Задача создана")
        entries = log.read("sess_001")
        assert len(entries) == 2
        assert entries[0]["role"] == "user"
        assert entries[0]["text"] == "Создай задачу купить молоко"
        assert entries[1]["role"] == "bot"
        assert "timestamp" in entries[0]

    def test_read_nonexistent(self, tmp_path):
        log = RawSessionLog(log_dir=tmp_path / "sessions")
        entries = log.read("nonexistent")
        assert entries == []

    def test_extra_fields(self, tmp_path):
        log = RawSessionLog(log_dir=tmp_path / "sessions")
        log.write("sess_002", "user", "тест", skill="задачник")
        entries = log.read("sess_002")
        assert entries[0]["skill"] == "задачник"

    def test_separate_sessions(self, tmp_path):
        log = RawSessionLog(log_dir=tmp_path / "sessions")
        log.write("s1", "user", "msg1")
        log.write("s2", "user", "msg2")
        assert len(log.read("s1")) == 1
        assert len(log.read("s2")) == 1
