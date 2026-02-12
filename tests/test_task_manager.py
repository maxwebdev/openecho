"""Tests for Task Manager handler — atom 6.5."""
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# handler.py is in skills/task-manager/ which isn't a standard package
# Import it by adding skills dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "task-manager"))

from handler import (
    handle, create_task, get_tasks, complete_task, delete_task,
    _extract_task_content, _extract_due, TodoistError,
)


@pytest.mark.unit
class TestExtractTaskContent:
    def test_simple(self):
        assert _extract_task_content("создай задачу купить молоко") == "купить молоко"

    def test_with_due(self):
        assert _extract_task_content("добавь задачу позвонить маме завтра") == "позвонить маме"

    def test_just_trigger(self):
        assert _extract_task_content("создай задачу") == ""

    def test_no_trigger(self):
        assert _extract_task_content("купить молоко") == "купить молоко"

    def test_with_na_segodnya(self):
        assert _extract_task_content("создай задачу сходить к врачу на сегодня") == "сходить к врачу"


@pytest.mark.unit
class TestExtractDue:
    def test_tomorrow(self):
        assert _extract_due("создай задачу завтра") == "tomorrow"

    def test_today(self):
        assert _extract_due("что на сегодня") == "today"

    def test_day_after(self):
        assert _extract_due("добавь на послезавтра") == "in 2 days"

    def test_next_week(self):
        assert _extract_due("через неделю") == "in 7 days"

    def test_no_due(self):
        assert _extract_due("создай задачу купить молоко") == ""


@pytest.mark.unit
class TestHandle:
    @pytest.mark.asyncio
    async def test_create_task(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "abc123",
            "content": "купить молоко",
            "due": {"date": "2025-02-13"},
        }

        with patch("handler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            with patch.dict("os.environ", {"TODOIST_API_TOKEN": "test_token"}):
                result = await handle("создай задачу купить молоко")

        assert result["type"] == "complete"
        assert result["done"] is True
        assert "купить молоко" in result["text"]

    @pytest.mark.asyncio
    async def test_create_empty_asks_question(self):
        with patch.dict("os.environ", {"TODOIST_API_TOKEN": "test_token"}):
            result = await handle("создай задачу")
        assert result["type"] == "question"
        assert result["done"] is False

    @pytest.mark.asyncio
    async def test_show_tasks(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "1", "content": "Купить молоко", "due": {"date": "2025-02-13"}, "priority": 1},
                {"id": "2", "content": "Позвонить маме", "due": None, "priority": 1},
            ]
        }

        with patch("handler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            with patch.dict("os.environ", {"TODOIST_API_TOKEN": "test_token"}):
                result = await handle("что у меня на сегодня")

        assert result["type"] == "complete"
        assert "Купить молоко" in result["text"]
        assert "Позвонить маме" in result["text"]

    @pytest.mark.asyncio
    async def test_show_empty_tasks(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch("handler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            with patch.dict("os.environ", {"TODOIST_API_TOKEN": "test_token"}):
                result = await handle("что на сегодня")

        assert result["type"] == "complete"
        assert "нет" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_complete_no_id_asks(self):
        with patch.dict("os.environ", {"TODOIST_API_TOKEN": "test_token"}):
            result = await handle("задача выполнена")
        assert result["type"] == "question"

    @pytest.mark.asyncio
    async def test_complete_with_id(self):
        mock_response = MagicMock()
        mock_response.status_code = 204

        with patch("handler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            with patch.dict("os.environ", {"TODOIST_API_TOKEN": "test_token"}):
                result = await handle("задача выполнена", context={"task_id": "abc123"})

        assert result["type"] == "complete"
        assert "завершена" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_delete_no_id_asks(self):
        with patch.dict("os.environ", {"TODOIST_API_TOKEN": "test_token"}):
            result = await handle("удали задачу")
        assert result["type"] == "question"

    @pytest.mark.asyncio
    async def test_no_token_error(self):
        with patch.dict("os.environ", {}, clear=True):
            result = await handle("создай задачу тест")
        assert result["type"] == "error"
        assert "TODOIST_API_TOKEN" in result["text"]

    @pytest.mark.asyncio
    async def test_api_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("handler.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            with patch.dict("os.environ", {"TODOIST_API_TOKEN": "test_token"}):
                result = await handle("создай задачу тест ошибки")

        assert result["type"] == "error"
