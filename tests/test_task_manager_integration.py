"""Integration tests for Task Manager — real Todoist API."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "task-manager"))

from handler import handle, create_task, get_tasks, delete_task


@pytest.mark.integration
class TestTodoistIntegration:
    @pytest.mark.asyncio
    async def test_create_and_delete(self):
        """Create a test task, verify it exists, then delete it."""
        result = await handle("создай задачу TEST OpenEcho integration")
        assert result["type"] == "complete"
        assert "TEST OpenEcho integration" in result["text"]

        # Get tasks to find ours
        tasks = await get_tasks(filter_str="all")
        test_tasks = [t for t in tasks if "TEST OpenEcho integration" in t["content"]]
        assert len(test_tasks) >= 1

        # Cleanup
        for t in test_tasks:
            await delete_task(t["id"])

    @pytest.mark.asyncio
    async def test_show_today(self):
        """Show today's tasks — should return without error."""
        result = await handle("что на сегодня")
        assert result["type"] == "complete"
        assert result["done"] is True
