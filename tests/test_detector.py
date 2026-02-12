"""Tests for src/input/detector.py — atom 1.1."""
import pytest
from unittest.mock import MagicMock

from src.input.detector import detect_type, MessageType


def _msg(**kwargs):
    """Create a mock aiogram Message with specified attributes."""
    m = MagicMock()
    m.text = kwargs.get("text")
    m.voice = kwargs.get("voice")
    m.video_note = kwargs.get("video_note")
    m.video = kwargs.get("video")
    m.photo = kwargs.get("photo")
    m.document = kwargs.get("document")
    m.forward_from = kwargs.get("forward_from")
    m.forward_from_chat = kwargs.get("forward_from_chat")
    m.forward_sender_name = kwargs.get("forward_sender_name")
    return m


@pytest.mark.unit
def test_text_message():
    msg = _msg(text="hello")
    assert detect_type(msg) == MessageType.TEXT


@pytest.mark.unit
def test_voice_message():
    msg = _msg(voice=MagicMock())
    assert detect_type(msg) == MessageType.VOICE


@pytest.mark.unit
def test_video_note_message():
    msg = _msg(video_note=MagicMock())
    assert detect_type(msg) == MessageType.VIDEO_NOTE


@pytest.mark.unit
def test_video_message():
    msg = _msg(video=MagicMock())
    assert detect_type(msg) == MessageType.VIDEO


@pytest.mark.unit
def test_photo_message():
    msg = _msg(photo=[MagicMock()])
    assert detect_type(msg) == MessageType.PHOTO


@pytest.mark.unit
def test_document_message():
    msg = _msg(document=MagicMock())
    assert detect_type(msg) == MessageType.DOCUMENT


@pytest.mark.unit
def test_forward_from_user():
    msg = _msg(forward_from=MagicMock(), text="forwarded text")
    assert detect_type(msg) == MessageType.FORWARD


@pytest.mark.unit
def test_forward_from_chat():
    msg = _msg(forward_from_chat=MagicMock())
    assert detect_type(msg) == MessageType.FORWARD


@pytest.mark.unit
def test_forward_sender_name():
    msg = _msg(forward_sender_name="John")
    assert detect_type(msg) == MessageType.FORWARD


@pytest.mark.unit
def test_unknown_message():
    msg = _msg()
    assert detect_type(msg) == MessageType.UNKNOWN
