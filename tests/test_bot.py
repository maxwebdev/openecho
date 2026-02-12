"""Tests for src/bot.py — atom 0.1."""
import pytest
from unittest.mock import AsyncMock, patch

from src.bot import cmd_start, on_message


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_returns_greeting():
    msg = AsyncMock()
    await cmd_start(msg)
    msg.answer.assert_called_once()
    text = msg.answer.call_args[0][0]
    assert "OpenEcho" in text


@pytest.mark.unit
@pytest.mark.asyncio
async def test_on_message_returns_placeholder():
    msg = AsyncMock()
    await on_message(msg)
    msg.answer.assert_called_once()
    text = msg.answer.call_args[0][0]
    assert "получено" in text.lower() or "Gateway" in text


@pytest.mark.unit
def test_create_bot_raises_without_token():
    from src.bot import create_bot
    with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": ""}, clear=False):
        with pytest.raises(RuntimeError):
            create_bot()
