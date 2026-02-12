"""Integration tests for src/bus.py — atom 0.2 (real Redis)."""
import asyncio
import pytest

from src.bus import EventBus


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_subscribe_real_redis():
    """Publish an event, subscribe picks it up."""
    bus_pub = EventBus("redis://localhost:6379/0")
    bus_sub = EventBus("redis://localhost:6379/0")

    received = []

    async def handler(data):
        received.append(data)

    # Start subscriber in background
    sub_task = asyncio.create_task(bus_sub.subscribe("test_ch", handler))
    await asyncio.sleep(0.3)  # let subscriber connect

    # Publish
    await bus_pub.publish("test_ch", {"msg": "hello"})
    await asyncio.sleep(0.3)  # let message arrive

    assert len(received) == 1
    assert received[0]["msg"] == "hello"

    # Cleanup
    await bus_sub.unsubscribe("test_ch")
    sub_task.cancel()
    try:
        await sub_task
    except (asyncio.CancelledError, Exception):
        pass
    await bus_pub.close()
    await bus_sub.close()
