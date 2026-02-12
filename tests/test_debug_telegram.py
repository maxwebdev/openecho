"""Tests for Debug Telegram — atom 10.1."""
import pytest

from src.debug.telegram import DebugManager


@pytest.mark.unit
class TestDebugManager:
    def test_enable_disable(self):
        dm = DebugManager()
        assert dm.is_enabled("user1") is False
        dm.enable("user1")
        assert dm.is_enabled("user1") is True
        dm.disable("user1")
        assert dm.is_enabled("user1") is False

    def test_disable_nonexistent(self):
        dm = DebugManager()
        dm.disable("user1")  # should not raise
        assert dm.is_enabled("user1") is False

    def test_multiple_users(self):
        dm = DebugManager()
        dm.enable("user1")
        dm.enable("user2")
        assert dm.is_enabled("user1") is True
        assert dm.is_enabled("user2") is True
        dm.disable("user1")
        assert dm.is_enabled("user1") is False
        assert dm.is_enabled("user2") is True

    def test_format_debug_block_empty(self):
        dm = DebugManager()
        assert dm.format_debug_block([]) == ""

    def test_format_debug_block(self):
        dm = DebugManager()
        events = [
            {"component": "gateway.level2", "action": "parse_intents",
             "llm_call": {"model": "haiku", "prompt_tokens": 280, "completion_tokens": 60}},
            {"component": "dispatcher", "action": "route_to_skill"},
        ]
        block = dm.format_debug_block(events)
        assert "──── debug ────" in block
        assert "gateway.level2" in block
        assert "haiku" in block
        assert "280+60 tok" in block
        assert "dispatcher" in block
        assert "───────────────" in block
