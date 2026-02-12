"""OpenEcho Gateway Level 2 — Intent Parser — atom 2.3.

Uses LLM (Haiku) to split user message into atomic intents.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "intent_prompt.md"


@dataclass
class ParsedIntent:
    """Single parsed intent."""
    text: str
    skill_hint: str = ""  # optional hint from LLM about which skill


@dataclass
class ParseResult:
    """Result of intent parsing."""
    intents: list[ParsedIntent] = field(default_factory=list)
    raw_response: str = ""
    tokens_used: int = 0


async def parse_intents(
    message: str,
    llm_call: Any = None,
    skill_names: list[str] | None = None,
) -> ParseResult:
    """Parse user message into atomic intents using LLM.

    Args:
        message: User message text.
        llm_call: Async callable(system_prompt, user_message) -> str.
                  If None, falls back to single-intent passthrough.
        skill_names: Available skill names for hints.
    """
    if llm_call is None:
        # No LLM available — treat entire message as one intent
        return ParseResult(intents=[ParsedIntent(text=message)])

    # Load system prompt
    system_prompt = _load_prompt(skill_names or [])

    try:
        raw = await llm_call(system_prompt, message)
        intents = _parse_response(raw)
        return ParseResult(intents=intents, raw_response=raw)
    except Exception as e:
        logger.error("Intent parsing failed: %s", e)
        # Fallback: treat as single intent
        return ParseResult(intents=[ParsedIntent(text=message)])


def _load_prompt(skill_names: list[str]) -> str:
    """Load and fill in the system prompt template."""
    if PROMPT_PATH.exists():
        template = PROMPT_PATH.read_text(encoding="utf-8")
    else:
        template = _default_prompt()

    skills_str = ", ".join(skill_names) if skill_names else "none loaded"
    return template.replace("{{SKILLS}}", skills_str)


def _default_prompt() -> str:
    return (
        "You are an intent parser. Split the user message into atomic intents.\n"
        "Available skills: {{SKILLS}}\n"
        "Return JSON array: [{\"text\": \"...\", \"skill_hint\": \"...\"}]\n"
        "If only one intent, return array with one element.\n"
        "Respond ONLY with valid JSON, no markdown."
    )


def _parse_response(raw: str) -> list[ParsedIntent]:
    """Parse LLM JSON response into ParsedIntent list."""
    # Strip markdown code blocks if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    data = json.loads(text)
    if isinstance(data, dict) and "intents" in data:
        data = data["intents"]
    if not isinstance(data, list):
        data = [data]

    return [
        ParsedIntent(
            text=item.get("text", "") if isinstance(item, dict) else str(item),
            skill_hint=item.get("skill_hint", "") if isinstance(item, dict) else "",
        )
        for item in data
    ]
