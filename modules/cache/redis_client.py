"""
Redis-клиент для кэша.
Если Redis недоступен — функции деградируют до no-op (кэш не работает).
"""
import json
import os
import logging
from typing import Any

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
logger = logging.getLogger(__name__)

_client: aioredis.Redis | None = None
_available: bool = False


async def init_redis() -> None:
    """Подключиться к Redis. Если недоступен — приложение работает без кэша."""
    global _client, _available
    try:
        _client = aioredis.from_url(REDIS_URL, decode_responses=True)
        await _client.ping()
        _available = True
        logger.info("Redis connected: %s", REDIS_URL)
    except Exception as e:
        logger.warning("Redis unavailable: %s — running without cache", e)
        _client = None
        _available = False


async def close_redis() -> None:
    global _client, _available
    if _client:
        await _client.close()
    _client = None
    _available = False


def is_available() -> bool:
    return _available


async def get_cached(key: str) -> Any | None:
    if not _available or not _client:
        return None
    try:
        raw = await _client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def set_cached(key: str, value: Any, ttl: int = 60) -> None:
    if not _available or not _client:
        return
    try:
        await _client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        pass


async def delete_cached(pattern: str) -> None:
    """Удалить ключи по паттерну (например, 'listings:*')."""
    if not _available or not _client:
        return
    try:
        async for key in _client.scan_iter(match=pattern):
            await _client.delete(key)
    except Exception:
        pass
