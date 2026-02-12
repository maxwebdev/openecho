"""Tests for src/skill_runtime/tools.py — atom 6.3."""
import pytest
from src.skill_runtime.tools import ToolRegistry, ToolError, create_default_registry


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_and_call():
    reg = ToolRegistry()

    async def my_tool(x: int) -> int:
        return x * 2

    reg.register("double", my_tool)
    assert reg.has("double")
    result = await reg.call("double", x=5)
    assert result == 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_unknown_tool():
    reg = ToolRegistry()
    with pytest.raises(ToolError, match="Unknown tool"):
        await reg.call("nonexistent")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tool_error_wrapped():
    reg = ToolRegistry()

    async def bad_tool():
        raise ValueError("boom")

    reg.register("bad", bad_tool)
    with pytest.raises(ToolError, match="failed"):
        await reg.call("bad")


@pytest.mark.unit
def test_list_tools():
    reg = ToolRegistry()

    async def t1(): pass
    async def t2(): pass

    reg.register("a", t1)
    reg.register("b", t2)
    assert sorted(reg.list_tools()) == ["a", "b"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_default_registry():
    reg = create_default_registry()
    assert reg.has("ask_user")
    assert reg.has("memory_search")
    assert reg.has("memory_get")
    assert reg.has("scheduler_set")

    result = await reg.call("ask_user", text="question?")
    assert result["type"] == "question"
