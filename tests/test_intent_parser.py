"""Tests for src/gateway/intent_parser.py — atom 2.3 (unit, mocked LLM)."""
import json
import pytest
from src.gateway.intent_parser import parse_intents, ParsedIntent, _parse_response


@pytest.mark.unit
@pytest.mark.asyncio
async def test_single_intent_no_llm():
    result = await parse_intents("создай задачу", llm_call=None)
    assert len(result.intents) == 1
    assert result.intents[0].text == "создай задачу"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_single_intent_with_llm():
    async def mock_llm(system, user):
        return json.dumps([{"text": "создать задачу купить молоко", "skill_hint": "task-manager"}])

    result = await parse_intents("создай задачу купить молоко", llm_call=mock_llm, skill_names=["task-manager"])
    assert len(result.intents) == 1
    assert "молоко" in result.intents[0].text
    assert result.intents[0].skill_hint == "task-manager"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_two_intents_with_llm():
    async def mock_llm(system, user):
        return json.dumps([
            {"text": "создать задачу купить молоко", "skill_hint": "task-manager"},
            {"text": "показать прогресс по целям", "skill_hint": ""},
        ])

    result = await parse_intents("создай задачу и кстати как прогресс", llm_call=mock_llm)
    assert len(result.intents) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_failure_fallback():
    async def bad_llm(system, user):
        raise Exception("API down")

    result = await parse_intents("test message", llm_call=bad_llm)
    assert len(result.intents) == 1
    assert result.intents[0].text == "test message"


@pytest.mark.unit
def test_parse_response_with_markdown():
    raw = '```json\n[{"text": "test", "skill_hint": ""}]\n```'
    intents = _parse_response(raw)
    assert len(intents) == 1
    assert intents[0].text == "test"


@pytest.mark.unit
def test_parse_response_dict_wrapper():
    raw = '{"intents": [{"text": "a"}, {"text": "b"}]}'
    intents = _parse_response(raw)
    assert len(intents) == 2
