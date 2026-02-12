"""Tests for Debug Web Console — atom 10.2."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.debug.web import app, broadcast_event, _events, _clients


@pytest.mark.unit
class TestDebugWeb:
    def test_app_routes(self):
        routes = [r.path for r in app.routes]
        assert "/debug" in routes
        assert "/ws" in routes
        assert "/debug/state" in routes

    @pytest.mark.asyncio
    async def test_broadcast_event(self):
        _events.clear()
        _clients.clear()
        event = {"component": "test", "action": "ping", "timestamp": "2025-01-01"}
        await broadcast_event(event)
        assert len(_events) == 1
        assert _events[0]["component"] == "test"

    @pytest.mark.asyncio
    async def test_broadcast_max_events(self):
        _events.clear()
        _clients.clear()
        for i in range(600):
            await broadcast_event({"n": i})
        assert len(_events) == 500  # MAX_EVENTS

    @pytest.mark.asyncio
    async def test_broadcast_to_client(self):
        _events.clear()
        _clients.clear()
        mock_ws = AsyncMock()
        _clients.append(mock_ws)
        await broadcast_event({"component": "test", "action": "hello"})
        mock_ws.send_text.assert_called_once()
        _clients.clear()
