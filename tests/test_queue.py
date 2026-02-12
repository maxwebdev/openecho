"""Tests for src/queue.py — atoms 3.1, 3.2, 3.3."""
import pytest
from src.queue import IntentQueue


@pytest.mark.unit
def test_add_and_pop():
    q = IntentQueue()
    q.add("task 1", priority=5)
    item = q.pop()
    assert item is not None
    assert item.text == "task 1"
    assert q.is_empty()


@pytest.mark.unit
def test_priority_order():
    q = IntentQueue()
    q.add("low priority", priority=10)
    q.add("high priority", priority=1)
    q.add("medium priority", priority=5)

    item1 = q.pop()
    item2 = q.pop()
    item3 = q.pop()

    assert item1.text == "high priority"
    assert item2.text == "medium priority"
    assert item3.text == "low priority"


@pytest.mark.unit
def test_fifo_same_priority():
    q = IntentQueue()
    q.add("first", priority=5)
    q.add("second", priority=5)
    q.add("third", priority=5)

    assert q.pop().text == "first"
    assert q.pop().text == "second"
    assert q.pop().text == "third"


@pytest.mark.unit
def test_pop_empty():
    q = IntentQueue()
    assert q.pop() is None


@pytest.mark.unit
def test_peek():
    q = IntentQueue()
    q.add("a", priority=3)
    q.add("b", priority=1)
    items = q.peek()
    assert len(items) == 2
    assert items[0].text == "b"  # higher priority first
    assert q.size() == 2  # peek does not remove


@pytest.mark.unit
def test_size_and_clear():
    q = IntentQueue()
    q.add("x")
    q.add("y")
    assert q.size() == 2
    q.clear()
    assert q.size() == 0
    assert q.is_empty()


@pytest.mark.unit
def test_skill_hint():
    q = IntentQueue()
    q.add("do stuff", priority=2, skill_hint="task-manager")
    item = q.pop()
    assert item.skill_hint == "task-manager"
