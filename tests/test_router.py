"""Tests for src/gateway/router.py — atom 2.5."""
import pytest
from src.gateway.router import route_intent, route_intents, RouteAction


@pytest.mark.unit
def test_no_active_skill_goes_to_queue():
    d = route_intent("создать задачу", skill_hint="task-manager", active_skill="", status="idle")
    assert d.action == RouteAction.TO_QUEUE


@pytest.mark.unit
def test_matching_skill_goes_direct():
    d = route_intent("создать задачу", skill_hint="task-manager", active_skill="task-manager", status="busy")
    assert d.action == RouteAction.TO_ACTIVE_SKILL


@pytest.mark.unit
def test_waiting_answer_no_hint_goes_to_active():
    d = route_intent("завтра", skill_hint="", active_skill="task-manager", status="waiting_answer")
    assert d.action == RouteAction.TO_ACTIVE_SKILL


@pytest.mark.unit
def test_different_skill_asks_confirmation():
    d = route_intent("проведи рефлексию", skill_hint="psychologist", active_skill="task-manager", status="busy")
    assert d.action == RouteAction.ASK_CONFIRMATION


@pytest.mark.unit
def test_route_multiple_intents():
    intents = [
        {"text": "создать задачу", "skill_hint": "task-manager"},
        {"text": "рефлексия", "skill_hint": "psychologist"},
    ]
    decisions = route_intents(intents, active_skill="", status="idle")
    assert len(decisions) == 2
    assert all(d.action == RouteAction.TO_QUEUE for d in decisions)
