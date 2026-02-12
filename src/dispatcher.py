"""OpenEcho Dispatcher — atoms 5.1-5.5.

Determines target skill for intent, launches it, handles completion/questions,
updates session state.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from src.config_loader import SkillConfig
from src.queue import IntentQueue, QueuedIntent
from src.session import SessionState

logger = logging.getLogger(__name__)


@dataclass
class SkillInput:
    """Input passed to a skill (matches Skill_Contract.md)."""
    intent: str
    user_id: str
    session_id: str
    context: dict[str, Any]


@dataclass
class SkillOutput:
    """Output from a skill."""
    type: str  # response, question, complete, error
    text: str
    done: bool
    report: str = ""


class Dispatcher:
    """Orchestrates skill execution."""

    def __init__(
        self,
        skill_registry: dict[str, SkillConfig],
        queue: IntentQueue,
        session: SessionState,
    ) -> None:
        self._registry = skill_registry
        self._queue = queue
        self._session = session
        self._skill_runner: Callable[..., Awaitable[SkillOutput]] | None = None

    def set_skill_runner(self, runner: Callable[..., Awaitable[SkillOutput]]) -> None:
        """Set the function that actually runs a skill."""
        self._skill_runner = runner

    def match_skill(self, intent_text: str, skill_hint: str = "") -> str | None:
        """Determine which skill handles the intent. Returns skill_id or None."""
        # If hint matches a known skill, use it
        if skill_hint and skill_hint in self._registry:
            return skill_hint

        # Search by triggers
        text_lower = intent_text.lower()
        best_match: str | None = None
        best_priority = 999

        for skill_id, config in self._registry.items():
            for trigger in config.triggers:
                trig_lower = trigger.lower()
                # Check if trigger root (first 4+ chars) appears in text
                # This handles Russian morphology: "задача" matches "задачу", "задачи"
                root = trig_lower[:min(4, len(trig_lower))]
                if root in text_lower or trig_lower in text_lower:
                    if config.priority < best_priority:
                        best_priority = config.priority
                        best_match = skill_id
                    break

        return best_match

    async def dispatch_next(self, user_id: str) -> SkillOutput | None:
        """Take next intent from queue and dispatch to skill."""
        item = self._queue.pop()
        if item is None:
            # Queue empty -> go idle
            await self._session.update(user_id, active_skill="", status="idle")
            return None

        skill_id = self.match_skill(item.text, item.skill_hint)
        if not skill_id:
            await self._session.update(user_id, active_skill="", status="idle")
            return SkillOutput(
                type="error",
                text=f"Не нашёл подходящий скилл для: {item.text}",
                done=True,
            )

        # Update state
        await self._session.update(user_id, active_skill=skill_id, status="busy")

        # Run skill
        if self._skill_runner:
            skill_input = SkillInput(
                intent=item.text,
                user_id=user_id,
                session_id=f"{user_id}_session",
                context={"timestamp": "", "source_message": item.text},
            )
            output = await self._skill_runner(skill_id, skill_input)
        else:
            output = SkillOutput(
                type="error",
                text="Skill runner not configured",
                done=True,
            )

        # Handle output
        return await self._handle_output(user_id, skill_id, output)

    async def handle_message_to_active(self, user_id: str, text: str) -> SkillOutput | None:
        """Forward message to currently active skill."""
        state = await self._session.get(user_id)
        skill_id = state.get("active_skill", "")
        if not skill_id or not self._skill_runner:
            return None

        skill_input = SkillInput(
            intent=text,
            user_id=user_id,
            session_id=f"{user_id}_session",
            context={"timestamp": "", "source_message": text},
        )
        output = await self._skill_runner(skill_id, skill_input)
        return await self._handle_output(user_id, skill_id, output)

    async def _handle_output(self, user_id: str, skill_id: str, output: SkillOutput) -> SkillOutput:
        """Process skill output: update state, chain next if done."""
        if output.done:
            # Skill finished — check queue for next
            if not self._queue.is_empty():
                await self._session.update(user_id, active_skill="", status="idle")
                # Caller should call dispatch_next again
            else:
                await self._session.update(user_id, active_skill="", status="idle")
        elif output.type == "question":
            await self._session.update(user_id, active_skill=skill_id, status="waiting_answer")

        return output
