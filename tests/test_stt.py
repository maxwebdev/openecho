"""Tests for src/input/stt.py — atom 1.2 (unit, mocked Deepgram)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.input.stt import transcribe_voice, STTError, graceful_stt_error


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transcribe_voice_no_api_key(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "")
    bot = AsyncMock()
    with pytest.raises(STTError, match="DEEPGRAM_API_KEY"):
        await transcribe_voice(bot, "file123")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transcribe_voice_download_failure(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
    bot = AsyncMock()
    bot.get_file = AsyncMock(side_effect=Exception("network error"))
    with pytest.raises(STTError, match="download"):
        await transcribe_voice(bot, "file123")


@pytest.mark.unit
def test_graceful_stt_error_returns_string():
    msg = graceful_stt_error()
    assert isinstance(msg, str)
    assert len(msg) > 10
