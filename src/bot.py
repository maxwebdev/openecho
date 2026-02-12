"""OpenEcho Telegram bot — atom 0.1.

Minimal aiogram 3.x bot with long polling.
Handlers: /start, message passthrough to Gateway (placeholder).
"""
from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

load_dotenv()

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    """Greet the user."""
    await message.answer(
        "👋 Привет! Я OpenEcho — твой AI-партнёр.\n"
        "Пока я умею немного, но скоро научусь большему."
    )


@router.message()
async def on_message(message: types.Message) -> None:
    """Catch-all handler — will route to Gateway later."""
    await message.answer("🔧 Сообщение получено. Gateway ещё не подключён.")


def create_bot() -> tuple[Bot, Dispatcher]:
    """Factory — create Bot and Dispatcher instances."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp


async def main() -> None:
    """Entry point."""
    logging.basicConfig(level=logging.INFO)
    bot, dp = create_bot()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
