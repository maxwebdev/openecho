"""Tests for src/gateway/fast_filter.py — atom 2.2."""
import pytest
from src.gateway.fast_filter import fast_filter, FilterDecision


@pytest.mark.unit
def test_no_active_skill():
    r = fast_filter("создай задачу", active_skill="", status="idle")
    assert r.decision == FilterDecision.TO_LEVEL2


@pytest.mark.unit
def test_simple_confirmation_to_active():
    r = fast_filter("да", active_skill="task-manager", status="waiting_answer")
    assert r.decision == FilterDecision.TO_ACTIVE_SKILL


@pytest.mark.unit
def test_simple_no_to_active():
    r = fast_filter("нет", active_skill="psychologist", status="busy")
    assert r.decision == FilterDecision.TO_ACTIVE_SKILL


@pytest.mark.unit
def test_multi_intent_to_level2():
    r = fast_filter("создай задачу и кстати как мой прогресс", active_skill="task-manager", status="busy")
    assert r.decision == FilterDecision.TO_LEVEL2


@pytest.mark.unit
def test_short_answer_waiting():
    r = fast_filter("завтра в 12", active_skill="task-manager", status="waiting_answer")
    assert r.decision == FilterDecision.TO_ACTIVE_SKILL


@pytest.mark.unit
def test_complex_message_to_level2():
    r = fast_filter("Мне нужно проанализировать мою переписку с женой и найти паттерны конфликтов",
                     active_skill="task-manager", status="busy")
    assert r.decision == FilterDecision.TO_LEVEL2


@pytest.mark.unit
def test_idle_always_level2():
    r = fast_filter("да", active_skill="task-manager", status="idle")
    assert r.decision == FilterDecision.TO_LEVEL2
