"""Tests for src/skill_runtime/contract.py — atom 6.4."""
import pytest
from src.skill_runtime.contract import validate_output, ContractError


@pytest.mark.unit
def test_valid_response():
    out = validate_output({"type": "response", "text": "Hello", "done": False})
    assert out.type == "response"
    assert out.text == "Hello"
    assert out.done is False


@pytest.mark.unit
def test_valid_complete():
    out = validate_output({"type": "complete", "text": "Done", "done": True, "report": "task created"})
    assert out.type == "complete"
    assert out.done is True
    assert out.report == "task created"


@pytest.mark.unit
def test_valid_question():
    out = validate_output({"type": "question", "text": "Which date?", "done": False})
    assert out.type == "question"


@pytest.mark.unit
def test_valid_error():
    out = validate_output({"type": "error", "text": "API down", "done": True})
    assert out.type == "error"
    assert out.done is True


@pytest.mark.unit
def test_missing_type():
    with pytest.raises(ContractError, match="type"):
        validate_output({"text": "no type"})


@pytest.mark.unit
def test_invalid_type():
    with pytest.raises(ContractError, match="Invalid type"):
        validate_output({"type": "unknown", "text": "x"})


@pytest.mark.unit
def test_not_a_dict():
    with pytest.raises(ContractError, match="dict"):
        validate_output("not a dict")


@pytest.mark.unit
def test_infer_done_from_type():
    out = validate_output({"type": "complete", "text": "ok"})
    assert out.done is True

    out2 = validate_output({"type": "response", "text": "ok"})
    assert out2.done is False
