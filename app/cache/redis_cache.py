from functools import lru_cache
import hashlib
import json
import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

logger = logging.getLogger("app.cache.redis")


class RedisCacheClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    def get_json(self, key: str) -> dict[str, Any] | None:
        try:
            raw = self._client.get(key)
        except RedisError:
            logger.exception("cache_read_failed", extra={"cache_key": key})
            return None

        if raw is None:
            return None

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.exception("cache_decode_failed", extra={"cache_key": key})
            return None

        if isinstance(payload, dict):
            return payload
        return None

    def set_json(self, key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        try:
            self._client.setex(key, ttl_seconds, json.dumps(payload, default=str))
        except RedisError:
            logger.exception("cache_write_failed", extra={"cache_key": key})


@lru_cache
def get_cache_client() -> RedisCacheClient | None:
    settings = get_settings()
    if not settings.redis_enabled:
        return None
    return RedisCacheClient()


def build_cache_key(prefix: str, **parts: object) -> str:
    key_parts = []
    for name in sorted(parts):
        value = str(parts[name])
        compact = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
        key_parts.append(f"{name}:{compact}")

    return f"aiiis:{prefix}:{':'.join(key_parts)}"
