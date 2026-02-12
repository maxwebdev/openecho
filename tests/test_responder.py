"""Tests for src/gateway/responder.py — atom 2.6."""
import pytest
from unittest.mock import AsyncMock

from src.gateway.responder import send_response, send_skill_response


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_response_normal():
    bot = AsyncMock()
    await send_response(bot, 123, "hello")
    bot.send_message.assert_called_once_with(123, "hello")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_response_empty():
    bot = AsyncMock()
    await send_response(bot, 123, "")
    bot.send_message.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_response_long():
    bot = AsyncMock()
    long_text = "A" * 5000
    await send_response(bot, 123, long_text)
    assert bot.send_message.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_skill_response():
    bot = AsyncMock()
    output = {"type": "response", "text": "Done!", "done": False}
    await send_skill_response(bot, 123, output)
    bot.send_message.assert_called_once_with(123, "Done!")
