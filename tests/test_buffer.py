"""Tests for src/gateway/buffer.py — atom 2.1."""
import pytest
from src.gateway.buffer import MessageBuffer, BufferItem


@pytest.mark.unit
def test_add_and_has_items():
    buf = MessageBuffer()
    assert not buf.has_items("u1")
    buf.add("u1", BufferItem(type="forwarded", data={"text": "hi"}))
    assert buf.has_items("u1")


@pytest.mark.unit
def test_collect_clears_buffer():
    buf = MessageBuffer()
    buf.add("u1", BufferItem(type="forwarded", data={"text": "a"}))
    buf.add("u1", BufferItem(type="forwarded", data={"text": "b"}))
    items = buf.collect("u1")
    assert len(items) == 2
    assert not buf.has_items("u1")


@pytest.mark.unit
def test_collect_empty():
    buf = MessageBuffer()
    items = buf.collect("u1")
    assert items == []


@pytest.mark.unit
def test_peek_does_not_clear():
    buf = MessageBuffer()
    buf.add("u1", BufferItem(type="photo", data={"file": "x"}))
    items = buf.peek("u1")
    assert len(items) == 1
    assert buf.has_items("u1")


@pytest.mark.unit
def test_clear():
    buf = MessageBuffer()
    buf.add("u1", BufferItem(type="forwarded"))
    buf.clear("u1")
    assert not buf.has_items("u1")


@pytest.mark.unit
def test_separate_users():
    buf = MessageBuffer()
    buf.add("u1", BufferItem(type="forwarded"))
    buf.add("u2", BufferItem(type="photo"))
    assert buf.has_items("u1")
    assert buf.has_items("u2")
    buf.collect("u1")
    assert not buf.has_items("u1")
    assert buf.has_items("u2")
