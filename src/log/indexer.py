"""OpenEcho Log Indexer — atom 8.3.

Processes session log via LLM to extract index cards for Memory.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "indexer_prompt.md"


def _load_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "Extract key facts, decisions, emotions from this session log.\n"
        "Return JSON array of index cards: [{id, skill, intent, summary, tags}]\n"
        "Only include meaningful information. Skip greetings and confirmations."
    )


def chunk_log(messages: list[dict[str, Any]], max_tokens: int = 3000) -> list[list[dict[str, Any]]]:
    """Split log into chunks if it exceeds max_tokens (rough estimate: 1 word ~ 1.3 tokens)."""
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_tokens = 0

    for msg in messages:
        text = msg.get("text", "")
        est_tokens = int(len(text.split()) * 1.3)
        if current_tokens + est_tokens > max_tokens and current:
            chunks.append(current)
            current = []
            current_tokens = 0
        current.append(msg)
        current_tokens += est_tokens

    if current:
        chunks.append(current)
    return chunks


async def index_session(
    messages: list[dict[str, Any]],
    llm_call: Any = None,
    session_id: str = "",
) -> list[dict[str, Any]]:
    """Process session log and return index cards.

    Args:
        messages: List of {role, text, timestamp} dicts.
        llm_call: Async callable(system_prompt, user_message) -> str.
        session_id: For card ID generation.
    """
    if not messages or llm_call is None:
        return []

    import json
    prompt = _load_prompt()
    chunks = chunk_log(messages)
    all_cards: list[dict[str, Any]] = []

    for i, chunk in enumerate(chunks):
        log_text = "\n".join(f"[{m.get('role', '?')}] {m.get('text', '')}" for m in chunk)
        try:
            raw = await llm_call(prompt, log_text)
            text = raw.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)
            cards = json.loads(text)
            if isinstance(cards, dict):
                cards = cards.get("cards", [cards])
            if not isinstance(cards, list):
                cards = [cards]
            for card in cards:
                if not card.get("id"):
                    card["id"] = f"{session_id}_chunk{i}_{len(all_cards)}"
            all_cards.extend(cards)
        except Exception as e:
            logger.error("Log indexing failed for chunk %d: %s", i, e)

    return all_cards
