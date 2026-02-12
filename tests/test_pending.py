"""Tests for src/pending.py — atoms 4.1, 4.2, 4.3."""
import pytest
from src.pending import PendingManager, PendingIntent


@pytest.mark.unit
def test_add_pending():
    pm = PendingManager()
    msg = pm.add("u1", PendingIntent(text="рефлексия", skill_hint="psychologist"))
    assert "рефлексия" in msg
    assert pm.has_pending("u1")


@pytest.mark.unit
def test_confirm():
    pm = PendingManager()
    pm.add("u1", PendingIntent(text="task1", skill_hint="task-manager"))
    intent = pm.confirm("u1")
    assert intent is not None
    assert intent.text == "task1"
    assert not pm.has_pending("u1")


@pytest.mark.unit
def test_reject():
    pm = PendingManager()
    pm.add("u1", PendingIntent(text="task1"))
    intent = pm.reject("u1")
    assert intent is not None
    assert intent.text == "task1"
    assert not pm.has_pending("u1")


@pytest.mark.unit
def test_confirm_empty():
    pm = PendingManager()
    assert pm.confirm("u1") is None


@pytest.mark.unit
def test_multiple_pending():
    pm = PendingManager()
    pm.add("u1", PendingIntent(text="a"))
    pm.add("u1", PendingIntent(text="b"))
    assert len(pm.peek("u1")) == 2
    pm.confirm("u1")  # removes "a"
    assert len(pm.peek("u1")) == 1
    assert pm.peek("u1")[0].text == "b"


@pytest.mark.unit
def test_clear():
    pm = PendingManager()
    pm.add("u1", PendingIntent(text="x"))
    pm.clear("u1")
    assert not pm.has_pending("u1")


@pytest.mark.unit
def test_separate_users():
    pm = PendingManager()
    pm.add("u1", PendingIntent(text="a"))
    pm.add("u2", PendingIntent(text="b"))
    pm.confirm("u1")
    assert not pm.has_pending("u1")
    assert pm.has_pending("u2")
