"""OpenEcho Session State — atom 0.3.

Stores per-user session state in Redis hashes.
Fields: active_skill, status, pending_intents.
"""
from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis


class SessionState:
    """Per-user session state backed by Redis hash."""

    PREFIX = "session:"

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis: aioredis.Redis = aioredis.from_url(redis_url)

    def _key(self, user_id: str) -> str:
        return f"{self.PREFIX}{user_id}"

    async def get(self, user_id: str) -> dict[str, Any]:
        """Return full session state for *user_id*."""
        raw = await self._redis.hgetall(self._key(user_id))
        if not raw:
            return self._default()
        result: dict[str, Any] = {}
        for k, v in raw.items():
            key = k.decode() if isinstance(k, bytes) else k
            val = v.decode() if isinstance(v, bytes) else v
            if key == "pending_intents":
                result[key] = json.loads(val)
            else:
                result[key] = val
        return result

    async def set(self, user_id: str, state: dict[str, Any]) -> None:
        """Overwrite session state for *user_id*."""
        data: dict[str, str] = {}
        for k, v in state.items():
            if isinstance(v, (list, dict)):
                data[k] = json.dumps(v, ensure_ascii=False)
            else:
                data[k] = str(v)
        key = self._key(user_id)
        await self._redis.delete(key)
        if data:
            await self._redis.hset(key, mapping=data)

    async def update(self, user_id: str, **fields: Any) -> None:
        """Update specific fields without touching others."""
        current = await self.get(user_id)
        current.update(fields)
        await self.set(user_id, current)

    async def clear(self, user_id: str) -> None:
        """Remove session state."""
        await self._redis.delete(self._key(user_id))

    async def close(self) -> None:
        """Close Redis connection."""
        await self._redis.aclose()

    @staticmethod
    def _default() -> dict[str, Any]:
        return {
            "active_skill": "",
            "status": "idle",
            "pending_intents": [],
        }
