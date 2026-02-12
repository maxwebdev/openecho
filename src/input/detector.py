"""OpenEcho Message Type Detector — atom 1.1.

Classifies incoming aiogram Message into a type:
text, voice, video_note, video, photo, forward, document, unknown.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message


class MessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    VIDEO = "video"
    PHOTO = "photo"
    FORWARD = "forward"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


def detect_type(message: "Message") -> MessageType:
    """Determine the type of an incoming Telegram message."""
    # Forwarded messages take priority
    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        return MessageType.FORWARD

    if message.voice:
        return MessageType.VOICE
    if message.video_note:
        return MessageType.VIDEO_NOTE
    if message.video:
        return MessageType.VIDEO
    if message.photo:
        return MessageType.PHOTO
    if message.document:
        return MessageType.DOCUMENT
    if message.text:
        return MessageType.TEXT

    return MessageType.UNKNOWN
