"""OpenEcho Forward Extractor — atom 1.4.

Extract sender info and text from forwarded messages.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class ForwardedContent:
    """Extracted data from a forwarded message."""
    sender: str
    text: str


def extract_forward(message: "Message") -> ForwardedContent:
    """Extract sender and text from a forwarded message."""
    # Determine sender name
    if message.forward_from:
        user = message.forward_from
        sender = user.full_name or user.username or str(user.id)
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        sender = chat.title or chat.username or str(chat.id)
    elif message.forward_sender_name:
        sender = message.forward_sender_name
    else:
        sender = "Unknown"

    # Extract text content
    text = message.text or message.caption or ""

    return ForwardedContent(sender=sender, text=text)
