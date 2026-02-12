"""Tests for src/input/video_stt.py — atom 1.3 (unit, mocked)."""
import pytest
from unittest.mock import AsyncMock

from src.input.stt import STTError
from src.input.video_stt import transcribe_video


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transcribe_video_no_api_key(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "")
    bot = AsyncMock()
    with pytest.raises(STTError, match="DEEPGRAM_API_KEY"):
        await transcribe_video(bot, "file123")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transcribe_video_download_failure(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
    bot = AsyncMock()
    bot.get_file = AsyncMock(side_effect=Exception("network error"))
    with pytest.raises(STTError, match="Video transcription failed"):
        await transcribe_video(bot, "file123")
