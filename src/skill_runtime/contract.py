"""OpenEcho Skill Contract — atom 6.4.

Validates skill output format: response, question, complete, error.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ContractError(Exception):
    """Raised when skill output violates the contract."""


VALID_TYPES = {"response", "question", "complete", "error"}


@dataclass
class ValidatedOutput:
    """Validated skill output."""
    type: str
    text: str
    done: bool
    report: str = ""


def validate_output(raw: dict[str, Any]) -> ValidatedOutput:
    """Validate a skill output dict against the contract.

    Expected format:
    {
        "type": "response" | "question" | "complete" | "error",
        "text": str,
        "done": bool,
        "report": str (optional, for "complete")
    }
    """
    if not isinstance(raw, dict):
        raise ContractError(f"Expected dict, got {type(raw).__name__}")

    output_type = raw.get("type")
    if not output_type:
        raise ContractError("Missing 'type' field")
    if output_type not in VALID_TYPES:
        raise ContractError(f"Invalid type '{output_type}', expected one of {VALID_TYPES}")

    text = raw.get("text", "")
    if not isinstance(text, str):
        raise ContractError(f"'text' must be string, got {type(text).__name__}")

    done = raw.get("done")
    if done is None:
        # Infer done from type
        done = output_type in ("complete", "error")
    if not isinstance(done, bool):
        raise ContractError(f"'done' must be bool, got {type(done).__name__}")

    report = raw.get("report", "")

    return ValidatedOutput(
        type=output_type,
        text=text,
        done=done,
        report=report,
    )
