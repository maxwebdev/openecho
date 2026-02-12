"""Tests for Log Filter — atom 8.1."""
import pytest

from src.log.filter import is_junk, filter_messages


@pytest.mark.unit
class TestLogFilter:
    def test_junk_yes(self):
        assert is_junk("да") is True
        assert is_junk("Да") is True
        assert is_junk("ок") is True
        assert is_junk("ага") is True

    def test_junk_empty(self):
        assert is_junk("") is True
        assert is_junk("   ") is True

    def test_not_junk(self):
        assert is_junk("создай задачу купить молоко") is False
        assert is_junk("как мой прогресс по целям") is False
        assert is_junk("проанализируй нашу беседу") is False

    def test_english_junk(self):
        assert is_junk("yes") is True
        assert is_junk("no") is True
        assert is_junk("ok") is True

    def test_filter_messages(self):
        messages = ["да", "создай задачу", "ок", "как дела с прогрессом", ""]
        result = filter_messages(messages)
        assert result == ["создай задачу", "как дела с прогрессом"]

    def test_filter_all_junk(self):
        messages = ["да", "ок", "ага"]
        result = filter_messages(messages)
        assert result == []
