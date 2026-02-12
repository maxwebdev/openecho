"""OpenEcho Task Manager Skill — handler.

CRUD operations for Todoist via REST API v1.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

BASE_URL = "https://api.todoist.com/api/v1"


class TodoistError(Exception):
    """Todoist API error."""


def _get_token() -> str:
    token = os.getenv("TODOIST_API_TOKEN", "")
    if not token:
        raise TodoistError("TODOIST_API_TOKEN not set")
    return token


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_get_token()}"}


async def create_task(content: str, due_string: str = "", project_id: str = "") -> dict[str, Any]:
    """Create a task in Todoist."""
    payload: dict[str, Any] = {"content": content}
    if due_string:
        payload["due_string"] = due_string
    if project_id:
        payload["project_id"] = project_id

    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/tasks", headers=_headers(), json=payload)
        if r.status_code not in (200, 201):
            raise TodoistError(f"Create failed: {r.status_code} {r.text[:200]}")
        task = r.json()
        return {
            "id": task["id"],
            "content": task["content"],
            "due": task.get("due", {}).get("date") if task.get("due") else None,
        }


async def get_tasks(filter_str: str = "today", project_id: str = "") -> list[dict[str, Any]]:
    """Get tasks from Todoist. Default: today's tasks."""
    params: dict[str, str] = {}
    if filter_str:
        params["filter"] = filter_str
    if project_id:
        params["project_id"] = project_id

    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/tasks", headers=_headers(), params=params)
        if r.status_code != 200:
            raise TodoistError(f"Get failed: {r.status_code} {r.text[:200]}")
        data = r.json()
        results = data.get("results", []) if isinstance(data, dict) else data
        return [
            {
                "id": t["id"],
                "content": t["content"],
                "due": t.get("due", {}).get("date") if t.get("due") else None,
                "priority": t.get("priority", 1),
            }
            for t in results
        ]


async def complete_task(task_id: str) -> bool:
    """Mark a task as completed."""
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/tasks/{task_id}/close", headers=_headers())
        if r.status_code not in (200, 204):
            raise TodoistError(f"Complete failed: {r.status_code} {r.text[:200]}")
        return True


async def delete_task(task_id: str) -> bool:
    """Delete a task."""
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{BASE_URL}/tasks/{task_id}", headers=_headers())
        if r.status_code not in (200, 204):
            raise TodoistError(f"Delete failed: {r.status_code} {r.text[:200]}")
        return True


async def get_projects() -> list[dict[str, Any]]:
    """Get all projects."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/projects", headers=_headers())
        if r.status_code != 200:
            raise TodoistError(f"Projects failed: {r.status_code} {r.text[:200]}")
        data = r.json()
        results = data.get("results", []) if isinstance(data, dict) else data
        return [
            {"id": p["id"], "name": p["name"]}
            for p in results
        ]


async def handle(intent: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Main handler - dispatches intent to the right action.

    Returns a skill contract response dict.
    """
    text = intent.lower().strip()

    try:
        # Create task
        if any(w in text for w in ["создай", "добав", "новая", "запиши"]):
            content = _extract_task_content(intent)
            if not content:
                return {
                    "type": "question",
                    "text": "Что записать в задачу?",
                    "done": False,
                }
            due = _extract_due(text)
            result = await create_task(content, due_string=due)
            due_text = f" на {result['due']}" if result.get("due") else ""
            return {
                "type": "complete",
                "text": f"Задача создана{due_text}: {result['content']}",
                "done": True,
            }

        # Show tasks
        if any(w in text for w in ["покаж", "что на", "список", "задачи", "сегодня"]):
            filter_str = "today" if ("сегодня" in text or "на сегодня" in text) else "all"
            tasks = await get_tasks(filter_str=filter_str)
            if not tasks:
                return {
                    "type": "complete",
                    "text": "Задач нет. Свободный день!",
                    "done": True,
                }
            lines = []
            for i, t in enumerate(tasks, 1):
                due_mark = f" ({t['due']})" if t.get("due") else ""
                lines.append(f"{i}. {t['content']}{due_mark}")
            return {
                "type": "complete",
                "text": "\n".join(lines),
                "done": True,
            }

        # Complete task
        if any(w in text for w in ["выполн", "готово", "закрой", "сделал", "завершил"]):
            task_id = (context or {}).get("task_id", "")
            if not task_id:
                return {
                    "type": "question",
                    "text": "Какую задачу завершить? Напиши номер или название.",
                    "done": False,
                }
            await complete_task(task_id)
            return {
                "type": "complete",
                "text": "Задача завершена.",
                "done": True,
            }

        # Delete task
        if any(w in text for w in ["удали", "убери", "отмени"]):
            task_id = (context or {}).get("task_id", "")
            if not task_id:
                return {
                    "type": "question",
                    "text": "Какую задачу удалить?",
                    "done": False,
                }
            await delete_task(task_id)
            return {
                "type": "complete",
                "text": "Задача удалена.",
                "done": True,
            }

        # Fallback: show today
        tasks = await get_tasks(filter_str="today")
        if not tasks:
            return {
                "type": "complete",
                "text": "Не понял команду. Задач на сегодня нет.",
                "done": True,
            }
        lines = [f"{i}. {t['content']}" for i, t in enumerate(tasks, 1)]
        return {
            "type": "complete",
            "text": "Вот задачи на сегодня:\n" + "\n".join(lines),
            "done": True,
        }

    except TodoistError as e:
        return {
            "type": "error",
            "text": f"Ошибка Todoist: {e}",
            "done": True,
        }
    except Exception as e:
        return {
            "type": "error",
            "text": f"Неожиданная ошибка: {e}",
            "done": True,
        }


def _extract_task_content(intent: str) -> str:
    """Extract task content from intent text.

    'создай задачу купить молоко' -> 'купить молоко'
    'добавь задачу позвонить маме завтра' -> 'позвонить маме'
    """
    text = intent.strip()
    triggers = [
        "создай задачу", "добавь задачу", "новая задача", "запиши задачу",
        "создай", "добавь", "запиши",
    ]
    lower = text.lower()
    for trigger in triggers:
        if lower.startswith(trigger):
            text = text[len(trigger):].strip()
            break

    # Remove due markers at the end
    due_markers = [
        "на послезавтра", "на завтра", "на сегодня",
        "послезавтра", "завтра", "сегодня",
        "через неделю", "на следующей неделе",
    ]
    lower_text = text.lower()
    for marker in due_markers:
        if lower_text.endswith(marker):
            text = text[:-len(marker)].strip()
            break

    return text


def _extract_due(text: str) -> str:
    """Extract due date hint from text for Todoist due_string."""
    if "послезавтра" in text:
        return "in 2 days"
    if "завтра" in text:
        return "tomorrow"
    if "сегодня" in text:
        return "today"
    if "через неделю" in text:
        return "in 7 days"
    if "следующ" in text and "недел" in text:
        return "next week"
    return ""
