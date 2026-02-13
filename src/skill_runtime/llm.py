"""OpenEcho LLM Adapter — atom 6.2.

Unified interface to Anthropic API (Haiku/Sonnet/Opus) with retry and backoff.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Model name mapping
MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-5-20250929",
    "opus": "claude-opus-4-6",
}


class LLMError(Exception):
    """Raised when LLM call fails after retries."""


async def call_llm(
    system_prompt: str,
    user_message: str,
    model: str = "haiku",
    max_tokens: int = 1000,
    temperature: float = 0.3,
    max_retries: int = 3,
    api_key: str | None = None,
) -> str:
    """Call Anthropic API and return the text response.

    Args:
        system_prompt: System prompt for the model.
        user_message: User message.
        model: Model alias (haiku, sonnet, opus) or full model name.
        max_tokens: Max tokens in response.
        temperature: Sampling temperature.
        max_retries: Number of retries on failure.
        api_key: Anthropic API key (falls back to env var).

    Returns:
        Model response text.

    Raises:
        LLMError on failure after retries.
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise LLMError("ANTHROPIC_API_KEY is not set")

    model_id = MODEL_MAP.get(model, model)

    import httpx

    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model_id,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["content"][0]["text"]
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning("LLM call failed (attempt %d/%d): %s, retrying in %ds",
                              attempt + 1, max_retries, e, wait)
                await asyncio.sleep(wait)

    raise LLMError(f"LLM call failed after {max_retries} retries: {last_error}")


def graceful_llm_error() -> str:
    """User-friendly message when LLM is unavailable."""
    return "Сервис временно недоступен. Попробуй через минуту."
