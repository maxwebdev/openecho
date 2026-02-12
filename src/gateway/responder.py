"""OpenEcho Gateway Responder — atom 2.6.

Accepts skill response and sends it to Telegram via bot.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiogram import Bot


async def send_response(bot: "Bot", chat_id: int, text: str) -> None:
    """Send text response to Telegram chat."""
    if not text:
        return
    # Telegram limit is 4096 chars
    if len(text) <= 4096:
        await bot.send_message(chat_id, text)
    else:
        # Split into chunks
        for i in range(0, len(text), 4096):
            await bot.send_message(chat_id, text[i:i + 4096])


async def send_skill_response(
    bot: "Bot",
    chat_id: int,
    skill_output: dict[str, Any],
    debug_mode: bool = False,
) -> None:
    """Process skill output and send to user.

    skill_output format: {type, text, done, report?}
    """
    text = skill_output.get("text", "")
    await send_response(bot, chat_id, text)

    # If debug mode, append debug info (placeholder)
    if debug_mode and skill_output.get("_debug"):
        debug_text = f"\n──── debug ────\n{skill_output['_debug']}\n───────────────"
        await send_response(bot, chat_id, debug_text)
