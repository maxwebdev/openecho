"""OpenEcho STT — atom 1.2.

Download voice from Telegram, send to Deepgram API, return text.
Graceful degradation: if Deepgram is unavailable, return error message.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


class STTError(Exception):
    """Raised when speech-to-text fails."""


async def _download_telegram_file(bot: "Bot", file_id: str) -> str:
    """Download file from Telegram, return temp file path."""
    file = await bot.get_file(file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name
    await bot.download_file(file.file_path, tmp_path)
    return tmp_path


async def transcribe_voice(bot: "Bot", file_id: str) -> str:
    """Download voice file from Telegram and transcribe via Deepgram.

    Returns transcribed text.
    Raises STTError on failure.
    """
    api_key = os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise STTError("DEEPGRAM_API_KEY is not set")

    # Download from Telegram
    tmp_path = ""
    try:
        tmp_path = await _download_telegram_file(bot, file_id)
    except Exception as e:
        raise STTError(f"Failed to download voice from Telegram: {e}") from e

    # Transcribe with Deepgram
    try:
        text = await _deepgram_transcribe(api_key, tmp_path, "audio/ogg")
        if not text:
            raise STTError("Deepgram returned empty transcript")
        return text
    except STTError:
        raise
    except Exception as e:
        raise STTError(f"Deepgram transcription failed: {e}") from e
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


async def _deepgram_transcribe(api_key: str, file_path: str, mimetype: str) -> str:
    """Call Deepgram REST API to transcribe audio file."""
    import httpx

    with open(file_path, "rb") as f:
        audio_data = f.read()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.deepgram.com/v1/listen",
            params={"language": "ru", "model": "nova-2", "smart_format": "true"},
            headers={
                "Authorization": f"Token {api_key}",
                "Content-Type": mimetype,
            },
            content=audio_data,
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["results"]["channels"][0]["alternatives"][0]["transcript"]


def graceful_stt_error() -> str:
    """User-friendly message when STT fails."""
    return "Не удалось распознать голосовое сообщение. Пришли текстом, пожалуйста."
