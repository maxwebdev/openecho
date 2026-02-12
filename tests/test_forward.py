"""Tests for src/input/forward.py — atom 1.4."""
import pytest
from unittest.mock import MagicMock

from src.input.forward import extract_forward, ForwardedContent


def _fwd_msg(forward_from=None, forward_from_chat=None, forward_sender_name=None, text=None, caption=None):
    m = MagicMock()
    m.forward_from = forward_from
    m.forward_from_chat = forward_from_chat
    m.forward_sender_name = forward_sender_name
    m.text = text
    m.caption = caption
    return m


@pytest.mark.unit
def test_forward_from_user():
    user = MagicMock()
    user.full_name = "Ivan Petrov"
    user.username = "ivan"
    user.id = 123
    msg = _fwd_msg(forward_from=user, text="Hello there")
    result = extract_forward(msg)
    assert result.sender == "Ivan Petrov"
    assert result.text == "Hello there"


@pytest.mark.unit
def test_forward_from_chat():
    chat = MagicMock()
    chat.title = "News Channel"
    chat.username = "news"
    chat.id = -100123
    msg = _fwd_msg(forward_from_chat=chat, text="Breaking news")
    result = extract_forward(msg)
    assert result.sender == "News Channel"
    assert result.text == "Breaking news"


@pytest.mark.unit
def test_forward_sender_name():
    msg = _fwd_msg(forward_sender_name="Hidden User", text="Secret")
    result = extract_forward(msg)
    assert result.sender == "Hidden User"


@pytest.mark.unit
def test_forward_caption():
    user = MagicMock()
    user.full_name = "Bob"
    msg = _fwd_msg(forward_from=user, caption="Photo caption")
    result = extract_forward(msg)
    assert result.text == "Photo caption"


@pytest.mark.unit
def test_forward_no_text():
    msg = _fwd_msg(forward_sender_name="X")
    result = extract_forward(msg)
    assert result.text == ""
