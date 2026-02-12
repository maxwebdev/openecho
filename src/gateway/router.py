"""OpenEcho Gateway Router — atom 2.5.

Routes parsed intents to:
- Active skill (if matches)
- Queue (if no skill active, or after confirmation)
- Pending confirmation (if new intent while skill is active)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RouteAction(str, Enum):
    TO_ACTIVE_SKILL = "to_active_skill"
    TO_QUEUE = "to_queue"
    TO_PENDING = "to_pending"
    ASK_CONFIRMATION = "ask_confirmation"


@dataclass
class RouteDecision:
    """Routing decision for a single intent."""
    action: RouteAction
    intent_text: str
    skill_hint: str = ""
    reason: str = ""


def route_intent(
    intent_text: str,
    skill_hint: str,
    active_skill: str,
    status: str,
) -> RouteDecision:
    """Decide where to send a single intent.

    Args:
        intent_text: The parsed intent text.
        skill_hint: LLM hint about target skill.
        active_skill: Currently active skill (empty = none).
        status: Session status (idle, busy, waiting_answer).
    """
    # No active skill -> straight to queue for dispatch
    if not active_skill or status == "idle":
        return RouteDecision(
            action=RouteAction.TO_QUEUE,
            intent_text=intent_text,
            skill_hint=skill_hint,
            reason="no active skill, queue for dispatch",
        )

    # Active skill exists
    # If hint matches active skill -> send directly
    if skill_hint and skill_hint == active_skill:
        return RouteDecision(
            action=RouteAction.TO_ACTIVE_SKILL,
            intent_text=intent_text,
            skill_hint=skill_hint,
            reason="matches active skill",
        )

    # If status is waiting_answer and no specific skill hint -> to active
    if status == "waiting_answer" and not skill_hint:
        return RouteDecision(
            action=RouteAction.TO_ACTIVE_SKILL,
            intent_text=intent_text,
            skill_hint=active_skill,
            reason="answer to waiting skill",
        )

    # Different skill needed while one is active -> ask confirmation
    return RouteDecision(
        action=RouteAction.ASK_CONFIRMATION,
        intent_text=intent_text,
        skill_hint=skill_hint,
        reason=f"new intent while {active_skill} is active",
    )


def route_intents(
    intents: list[dict[str, str]],
    active_skill: str,
    status: str,
) -> list[RouteDecision]:
    """Route a list of parsed intents."""
    decisions = []
    for intent in intents:
        d = route_intent(
            intent_text=intent.get("text", ""),
            skill_hint=intent.get("skill_hint", ""),
            active_skill=active_skill,
            status=status,
        )
        decisions.append(d)
    return decisions
