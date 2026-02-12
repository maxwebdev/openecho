"""OpenEcho Normalizer — atom 1.5.

Converts any message type into a unified format:
{text: str, type: MessageType, attachments: list[dict] | None}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from src.input.detector import MessageType

if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class NormalizedMessage:
    """Unified message format for the rest of the pipeline."""
    text: str
    type: MessageType
    user_id: int = 0
    attachments: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "text": self.text,
            "type": self.type.value,
            "user_id": self.user_id,
        }
        if self.attachments:
            result["attachments"] = self.attachments
        return result


def normalize(message: "Message", msg_type: MessageType, text: str = "") -> NormalizedMessage:
    """Normalize an aiogram Message into NormalizedMessage.

    Args:
        message: Raw aiogram message.
        msg_type: Detected message type.
        text: Pre-extracted text (e.g. from STT or forward extraction).
              If empty, falls back to message.text or message.caption.
    """
    final_text = text or message.text or message.caption or ""
    user_id = message.from_user.id if message.from_user else 0

    attachments = None
    if msg_type == MessageType.PHOTO and message.photo:
        attachments = [{"type": "photo", "file_id": message.photo[-1].file_id}]
    elif msg_type == MessageType.DOCUMENT and message.document:
        attachments = [{"type": "document", "file_id": message.document.file_id,
                        "file_name": message.document.file_name}]
    elif msg_type == MessageType.FORWARD:
        # Forward attachments handled separately via forward.py
        from src.input.forward import extract_forward
        fwd = extract_forward(message)
        attachments = [{"type": "forwarded", "from": fwd.sender, "text": fwd.text}]
        if not final_text:
            final_text = fwd.text

    return NormalizedMessage(
        text=final_text,
        type=msg_type,
        user_id=user_id,
        attachments=attachments,
    )
