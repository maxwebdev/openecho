"""OpenEcho Video STT — atom 1.3.

Download video/video_note from Telegram, extract audio with ffmpeg, transcribe via Deepgram.
Graceful degradation: if ffmpeg or Deepgram fails, return error message.
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from src.input.stt import STTError, _deepgram_transcribe, _download_telegram_file

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


async def transcribe_video(bot: "Bot", file_id: str, api_key: str = "") -> str:
    """Download video from Telegram, extract audio via ffmpeg, transcribe.

    Returns transcribed text.
    Raises STTError on failure.
    """
    import os
    if not api_key:
        api_key = os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise STTError("DEEPGRAM_API_KEY is not set")

    video_path = ""
    audio_path = ""
    try:
        # Download video from Telegram
        video_path = await _download_telegram_file(bot, file_id)

        # Extract audio with ffmpeg
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            audio_path = tmp.name

        result = subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libopus", "-y", audio_path],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise STTError(f"ffmpeg failed: {result.stderr.decode()[:200]}")

        # Transcribe with Deepgram
        text = await _deepgram_transcribe(api_key, audio_path, "audio/ogg")
        if not text:
            raise STTError("Deepgram returned empty transcript")
        return text

    except STTError:
        raise
    except subprocess.TimeoutExpired:
        raise STTError("ffmpeg timed out")
    except Exception as e:
        raise STTError(f"Video transcription failed: {e}") from e
    finally:
        if video_path:
            Path(video_path).unlink(missing_ok=True)
        if audio_path:
            Path(audio_path).unlink(missing_ok=True)
