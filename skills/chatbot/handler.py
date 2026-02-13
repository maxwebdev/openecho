"""OpenEcho Chatbot Skill — fallback handler.

Answers any message that doesn't match other skills, using LLM (Haiku).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.skill_runtime.llm import call_llm, LLMError

# Load prompt once
_prompt: str | None = None


def _get_prompt() -> str:
    global _prompt
    if _prompt is None:
        prompt_path = Path(__file__).parent / "prompt.md"
        _prompt = prompt_path.read_text(encoding="utf-8")
    return _prompt


async def handle(intent: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Handle a chatbot message via LLM."""
    try:
        response = await call_llm(
            system_prompt=_get_prompt(),
            user_message=intent,
            model="haiku",
            max_tokens=1000,
            temperature=0.5,
        )
        return {
            "type": "complete",
            "text": response,
            "done": True,
        }
    except LLMError as e:
        return {
            "type": "error",
            "text": f"Не удалось ответить: {e}",
            "done": True,
        }
