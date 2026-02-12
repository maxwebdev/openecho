"""OpenEcho Event Bus — atom 0.2.

Thin wrapper around Redis Pub/Sub for inter-component communication.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Awaitable

import redis.asyncio as aioredis


class EventBus:
    """Async event bus backed by Redis Pub/Sub."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis: aioredis.Redis = aioredis.from_url(redis_url)
        self._pubsub: aioredis.client.PubSub | None = None

    async def publish(self, channel: str, data: dict[str, Any]) -> int:
        """Publish a JSON-serialisable event to *channel*."""
        payload = json.dumps(data, ensure_ascii=False)
        return await self._redis.publish(channel, payload)

    async def subscribe(
        self,
        channel: str,
        callback: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        """Subscribe to *channel* and call *callback* for every event."""
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(channel)
        async for raw in self._pubsub.listen():
            if raw["type"] != "message":
                continue
            data = json.loads(raw["data"])
            await callback(data)

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from *channel*."""
        if self._pubsub:
            await self._pubsub.unsubscribe(channel)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._pubsub:
            await self._pubsub.aclose()
        await self._redis.aclose()
