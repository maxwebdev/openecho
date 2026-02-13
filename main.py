"""OpenEcho — main entry point.

Connects all components: Telegram bot -> Input -> Gateway -> Dispatcher -> Skill -> Response.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher as AiogramDP, Router, types
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv

load_dotenv()

# Add skills to path for handler imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "skills", "task-manager"))

from src.input.detector import detect_type, MessageType
from src.input.normalizer import normalize
from src.gateway.intent_parser import parse_intents
from src.gateway.responder import send_response
from src.skill_runtime.llm import call_llm
from src.dispatcher import Dispatcher as OpenEchoDispatcher, SkillOutput, SkillInput
from src.config_loader import load_skills
from src.session import SessionState
from src.queue import IntentQueue
from src.debug.telegram import DebugManager
from src.debug.web import app as debug_app, broadcast_event
import uvicorn

logger = logging.getLogger(__name__)
router = Router()

# Global components (initialized in main())
session: SessionState | None = None
dispatcher: OpenEchoDispatcher | None = None
debug_mgr = DebugManager()
bot_instance: Bot | None = None


async def _track(debug_events: list[dict], event: dict) -> None:
    """Append debug event locally and broadcast to web console."""
    debug_events.append(event)
    await broadcast_event(event)


async def run_skill(skill_id: str, skill_input: SkillInput) -> SkillOutput:
    """Execute a skill by its ID."""
    if skill_id == "task-manager":
        from handler import handle
        result = await handle(skill_input.intent, context=skill_input.context)
        return SkillOutput(
            type=result.get("type", "error"),
            text=result.get("text", ""),
            done=result.get("done", True),
        )
    return SkillOutput(type="error", text=f"Скилл '{skill_id}' пока не реализован", done=True)


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    await message.answer(
        "Привет! Я OpenEcho — твой AI-партнёр.\n"
        "Напиши мне что-нибудь, и я помогу."
    )


@router.message(Command("debug"))
async def cmd_debug(message: types.Message) -> None:
    """Toggle debug mode: /debug on | /debug off."""
    user_id = str(message.from_user.id)
    text = (message.text or "").strip().lower()
    if "on" in text:
        debug_mgr.enable(user_id)
        await message.answer("Debug: ON")
    elif "off" in text:
        debug_mgr.disable(user_id)
        await message.answer("Debug: OFF")
    else:
        status = "ON" if debug_mgr.is_enabled(user_id) else "OFF"
        await message.answer(f"Debug: {status}\n/debug on | /debug off")


@router.message()
async def on_message(message: types.Message) -> None:
    """Main message handler — full pipeline."""
    assert session is not None
    assert dispatcher is not None
    assert bot_instance is not None

    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    debug_events: list[dict] = []

    try:
        # 1. Input: detect type + normalize
        msg_type = detect_type(message)
        normalized = normalize(message, msg_type)
        text = normalized.text

        if not text:
            await message.answer("Не удалось обработать сообщение. Попробуй текстом.")
            return

        await _track(debug_events, {"component": "input", "action": f"type={msg_type.value}"})

        # 2. Gateway: read state
        state = await session.get(user_id)
        active_skill = state.get("active_skill", "")
        status = state.get("status", "idle")

        await _track(debug_events, {"component": "gateway.state", "action": f"skill={active_skill or 'none'}, status={status}"})

        # 3. If active skill is waiting for answer, forward directly
        if active_skill and status == "waiting_answer":
            output = await dispatcher.handle_message_to_active(user_id, text)
            if output:
                await _track(debug_events, {"component": "dispatcher", "action": f"forward to {active_skill}"})
                await _send_output(chat_id, output, debug_events, user_id)
                return

        # 4. Level 2: LLM intent parsing
        async def _llm_call(system: str, user: str) -> str:
            return await call_llm(system, user, model="haiku", max_tokens=300)

        skill_names = list(dispatcher._registry.keys())
        parse_result = await parse_intents(text, llm_call=_llm_call, skill_names=skill_names)

        await _track(debug_events, {
            "component": "gateway.level2",
            "action": f"intents={len(parse_result.intents)}: "
                      + "; ".join(pi.text[:40] for pi in parse_result.intents),
        })

        # 5. Queue parsed intents and dispatch
        for pi in parse_result.intents:
            skill_id = dispatcher.match_skill(pi.text, pi.skill_hint)
            if skill_id:
                config = dispatcher._registry.get(skill_id)
                pri = config.priority if config else 5
                dispatcher._queue.add(pi.text, priority=pri, skill_hint=skill_id)

        await _track(debug_events, {"component": "dispatcher", "action": f"queued={dispatcher._queue.size()}"})

        if dispatcher._queue.is_empty():
            await message.answer("Не понял, что сделать. Попробуй иначе.")
            await _send_debug(chat_id, debug_events, user_id)
            return

        # Dispatch all queued intents
        output = await dispatcher.dispatch_next(user_id)
        if output:
            await _send_output(chat_id, output, debug_events, user_id)

            while output and output.done and not dispatcher._queue.is_empty():
                output = await dispatcher.dispatch_next(user_id)
                if output:
                    await _send_output(chat_id, output, [], user_id)

    except Exception as e:
        logger.exception("Error processing message")
        await message.answer(f"Произошла ошибка: {e}")


async def _send_output(chat_id: int, output: SkillOutput, debug_events: list[dict], user_id: str) -> None:
    """Send skill output to user, with optional debug block."""
    assert bot_instance is not None
    if output.text:
        await send_response(bot_instance, chat_id, output.text)
    await _send_debug(chat_id, debug_events, user_id)


async def _send_debug(chat_id: int, debug_events: list[dict], user_id: str) -> None:
    """Send debug block if debug mode is on."""
    assert bot_instance is not None
    if debug_mgr.is_enabled(user_id) and debug_events:
        block = debug_mgr.format_debug_block(debug_events)
        if block:
            await send_response(bot_instance, chat_id, block)


async def main() -> None:
    """Initialize all components and start polling."""
    global session, dispatcher, bot_instance

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Session state
    session = SessionState(redis_url)
    logger.info("Redis session ready")

    # Load skill configs
    skills = load_skills()
    logger.info(f"Loaded {len(skills)} skills: {list(skills.keys())}")

    # Queue + Dispatcher
    queue = IntentQueue()
    dispatcher = OpenEchoDispatcher(skills, queue, session)
    dispatcher.set_skill_runner(run_skill)

    # Telegram bot
    bot_instance = Bot(token=token)
    dp = AiogramDP()
    dp.include_router(router)

    # Debug web console
    uvi_config = uvicorn.Config(debug_app, host="0.0.0.0", port=8484, log_level="warning")
    uvi_server = uvicorn.Server(uvi_config)
    asyncio.create_task(uvi_server.serve())
    logger.info("Debug web console on :8484")

    logger.info("Starting OpenEcho bot...")
    try:
        await dp.start_polling(bot_instance)
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
