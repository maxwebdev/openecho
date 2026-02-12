"""Tests for src/bus.py — atom 0.2 (unit, mocked Redis)."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.bus import EventBus


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_serializes_json():
    bus = EventBus.__new__(EventBus)
    bus._redis = AsyncMock()
    bus._redis.publish = AsyncMock(return_value=1)
    bus._pubsub = None

    data = {"type": "test", "value": 42}
    result = await bus.publish("ch1", data)

    bus._redis.publish.assert_called_once_with("ch1", json.dumps(data, ensure_ascii=False))
    assert result == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_unsubscribe_calls_pubsub():
    bus = EventBus.__new__(EventBus)
    bus._pubsub = AsyncMock()
    bus._redis = AsyncMock()

    await bus.unsubscribe("ch1")
    bus._pubsub.unsubscribe.assert_called_once_with("ch1")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_cleans_up():
    bus = EventBus.__new__(EventBus)
    bus._pubsub = AsyncMock()
    bus._redis = AsyncMock()

    await bus.close()
    bus._pubsub.aclose.assert_called_once()
    bus._redis.aclose.assert_called_once()
