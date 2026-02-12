"""Tests for src/dispatcher.py — atoms 5.1-5.5."""
import pytest
from unittest.mock import AsyncMock

from src.config_loader import SkillConfig
from src.queue import IntentQueue
from src.dispatcher import Dispatcher, SkillInput, SkillOutput


def _registry():
    return {
        "task-manager": SkillConfig(
            name="Задачник", type="executor", description="Tasks",
            triggers=["задача", "напомни", "что на сегодня"],
            priority=2,
        ),
        "psychologist": SkillConfig(
            name="Психолог", type="expert", description="Psychology",
            triggers=["рефлексия", "чувства", "тревога"],
            priority=5,
        ),
    }


@pytest.mark.unit
def test_match_skill_by_trigger():
    d = Dispatcher(_registry(), IntentQueue(), AsyncMock())
    assert d.match_skill("создай задачу") == "task-manager"
    assert d.match_skill("проведи рефлексию") == "psychologist"


@pytest.mark.unit
def test_match_skill_by_hint():
    d = Dispatcher(_registry(), IntentQueue(), AsyncMock())
    assert d.match_skill("do something", skill_hint="psychologist") == "psychologist"


@pytest.mark.unit
def test_match_skill_unknown():
    d = Dispatcher(_registry(), IntentQueue(), AsyncMock())
    assert d.match_skill("погода завтра") is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dispatch_next_empty_queue():
    session = AsyncMock()
    session.update = AsyncMock()
    d = Dispatcher(_registry(), IntentQueue(), session)
    result = await d.dispatch_next("u1")
    assert result is None
    session.update.assert_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dispatch_next_runs_skill():
    session = AsyncMock()
    session.update = AsyncMock()
    session.get = AsyncMock(return_value={"active_skill": "", "status": "idle", "pending_intents": []})

    q = IntentQueue()
    q.add("создай задачу купить молоко", priority=2, skill_hint="task-manager")

    async def mock_runner(skill_id, skill_input):
        assert skill_id == "task-manager"
        return SkillOutput(type="complete", text="Done!", done=True, report="task created")

    d = Dispatcher(_registry(), q, session)
    d.set_skill_runner(mock_runner)
    result = await d.dispatch_next("u1")

    assert result is not None
    assert result.type == "complete"
    assert result.done is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dispatch_question_sets_waiting():
    session = AsyncMock()
    session.update = AsyncMock()

    q = IntentQueue()
    q.add("создай задачу", priority=2, skill_hint="task-manager")

    async def mock_runner(skill_id, skill_input):
        return SkillOutput(type="question", text="На какую дату?", done=False)

    d = Dispatcher(_registry(), q, session)
    d.set_skill_runner(mock_runner)
    result = await d.dispatch_next("u1")

    assert result.type == "question"
    # Check session was set to waiting_answer
    calls = [c for c in session.update.call_args_list if "waiting_answer" in str(c)]
    assert len(calls) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dispatch_no_skill_found():
    session = AsyncMock()
    session.update = AsyncMock()

    q = IntentQueue()
    q.add("погода завтра", priority=5, skill_hint="")

    d = Dispatcher(_registry(), q, session)
    result = await d.dispatch_next("u1")

    assert result is not None
    assert result.type == "error"
    assert result.done is True
