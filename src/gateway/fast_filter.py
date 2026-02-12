"""OpenEcho Gateway Level 1 — Fast Filter — atom 2.2.

If a skill is active and message is simple -> route directly to skill.
Otherwise -> escalate to Level 2 (intent parser).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class FilterDecision(str, Enum):
    TO_ACTIVE_SKILL = "to_active_skill"
    TO_LEVEL2 = "to_level2"


# Patterns that indicate multi-intent messages
MULTI_INTENT_PATTERNS = [
    r"\bи кстати\b",
    r"\bа ещё\b",
    r"\bа еще\b",
    r"\bкстати\b",
    r"\bтакже\b",
    r"\bплюс ещё\b",
    r"\bплюс еще\b",
    r"\bи ещё\b",
    r"\bи еще\b",
]
_multi_re = re.compile("|".join(MULTI_INTENT_PATTERNS), re.IGNORECASE)

# Simple confirmation / short replies
SIMPLE_PATTERNS = [
    r"^да$", r"^нет$", r"^ок$", r"^ладно$", r"^хорошо$",
    r"^конечно$", r"^давай$", r"^отмена$", r"^стоп$",
    r"^yes$", r"^no$", r"^ok$",
]
_simple_re = re.compile("|".join(SIMPLE_PATTERNS), re.IGNORECASE)

# Max length for "simple" message (word count)
SIMPLE_MAX_WORDS = 5


@dataclass
class FilterResult:
    decision: FilterDecision
    reason: str


def fast_filter(text: str, active_skill: str, status: str) -> FilterResult:
    """Decide whether message goes to active skill or to Level 2.

    Args:
        text: Normalized message text.
        active_skill: Currently active skill name (empty = none).
        status: Session status (idle, busy, waiting_answer).
    """
    # No active skill -> always Level 2
    if not active_skill or status == "idle":
        return FilterResult(FilterDecision.TO_LEVEL2, "no active skill")

    # Multi-intent patterns -> Level 2
    if _multi_re.search(text):
        return FilterResult(FilterDecision.TO_LEVEL2, "multi-intent detected")

    # Simple reply / confirmation -> active skill
    stripped = text.strip()
    if _simple_re.match(stripped):
        return FilterResult(FilterDecision.TO_ACTIVE_SKILL, "simple confirmation")

    # Short message while skill is waiting for answer -> active skill
    word_count = len(stripped.split())
    if status == "waiting_answer" and word_count <= SIMPLE_MAX_WORDS:
        return FilterResult(FilterDecision.TO_ACTIVE_SKILL, "short answer to active skill")

    # Anything else -> Level 2 to be safe
    return FilterResult(FilterDecision.TO_LEVEL2, "complex message")
