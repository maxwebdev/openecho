"""Tests for src/input/normalizer.py — atom 1.5."""
import pytest
from unittest.mock import MagicMock

from src.input.detector import MessageType
from src.input.normalizer import normalize, NormalizedMessage


def _msg(text=None, caption=None, user_id=42, photo=None, document=None,
         forward_from=None, forward_sender_name=None):
    m = MagicMock()
    m.text = text
    m.caption = caption
    m.from_user = MagicMock()
    m.from_user.id = user_id
    m.photo = photo
    m.document = document
    m.forward_from = forward_from
    m.forward_from_chat = None
    m.forward_sender_name = forward_sender_name
    return m


@pytest.mark.unit
def test_normalize_text():
    msg = _msg(text="hello world")
    result = normalize(msg, MessageType.TEXT)
    assert result.text == "hello world"
    assert result.type == MessageType.TEXT
    assert result.user_id == 42
    assert result.attachments is None


@pytest.mark.unit
def test_normalize_voice_with_stt_text():
    msg = _msg()
    result = normalize(msg, MessageType.VOICE, text="transcribed text")
    assert result.text == "transcribed text"
    assert result.type == MessageType.VOICE


@pytest.mark.unit
def test_normalize_photo():
    photo = MagicMock()
    photo.file_id = "photo123"
    msg = _msg(photo=[photo], caption="my cat")
    result = normalize(msg, MessageType.PHOTO)
    assert result.text == "my cat"
    assert result.attachments is not None
    assert result.attachments[0]["type"] == "photo"


@pytest.mark.unit
def test_normalize_document():
    doc = MagicMock()
    doc.file_id = "doc123"
    doc.file_name = "report.pdf"
    msg = _msg(document=doc, caption="report")
    result = normalize(msg, MessageType.DOCUMENT)
    assert result.attachments[0]["file_name"] == "report.pdf"


@pytest.mark.unit
def test_normalize_forward():
    user = MagicMock()
    user.full_name = "Wife"
    user.username = None
    user.id = 99
    msg = _msg(forward_from=user, text="You are late again")
    result = normalize(msg, MessageType.FORWARD)
    assert result.attachments is not None
    assert result.attachments[0]["from"] == "Wife"
    assert result.text == "You are late again"


@pytest.mark.unit
def test_to_dict():
    msg = _msg(text="test")
    result = normalize(msg, MessageType.TEXT)
    d = result.to_dict()
    assert d["text"] == "test"
    assert d["type"] == "text"
    assert "attachments" not in d
