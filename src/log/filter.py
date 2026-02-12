"""OpenEcho Log Filter — atom 8.1.

Heuristic filter: short confirmations like "yes", "ok", "aga" are discarded.
"""
from __future__ import annotations

import re

JUNK_PATTERNS = [
    r"^да$", r"^нет$", r"^ок$", r"^ладно$", r"^хорошо$", r"^ага$",
    r"^угу$", r"^ну$", r"^ясно$", r"^понял$", r"^окей$",
    r"^yes$", r"^no$", r"^ok$", r"^yep$",
]
_junk_re = re.compile("|".join(JUNK_PATTERNS), re.IGNORECASE)

MIN_USEFUL_WORDS = 3


def is_junk(text: str) -> bool:
    """Return True if the message is junk (confirmation, too short)."""
    stripped = text.strip()
    if not stripped:
        return True
    if _junk_re.match(stripped):
        return True
    return False


def filter_messages(messages: list[str]) -> list[str]:
    """Filter out junk messages, return useful ones."""
    return [m for m in messages if not is_junk(m)]
