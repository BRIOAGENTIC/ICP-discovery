"""TTL cache layer (in-memory by default; Redis-ready interface)."""
import hashlib
import json
import logging
from typing import Any, Optional

from cachetools import TTLCache

from app.config import settings

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, ttl_seconds: int, maxsize: int = 1000):
        self._mem = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self._redis = None
        if settings.redis_url:
            try:
                import redis  # type: ignore

                self._redis = redis.from_url(
                    settings.redis_url, decode_responses=True
                )
                self._redis.ping()
                logger.info("Redis cache connected.")
            except Exception as e:  # pragma: no cover
                logger.warning(
                    "Redis unavailable (%s); falling back to in-memory.", e
                )
                self._redis = None

    @staticmethod
    def _key(parts: dict) -> str:
        blob = json.dumps(parts, sort_keys=True, default=str)
        return "icp:" + hashlib.sha256(blob.encode()).hexdigest()

    def get(self, key_parts: dict) -> Optional[Any]:
        key = self._key(key_parts)
        if self._redis:
            raw = self._redis.get(key)
            if raw:
                try:
                    return json.loads(raw)
                except Exception:
                    return None
        return self._mem.get(key)

    def set(self, key_parts: dict, value: Any) -> None:
        key = self._key(key_parts)
        if self._redis:
            try:
                self._redis.setex(key, settings.cache_ttl_seconds, json.dumps(value))
            except Exception as e:  # pragma: no cover
                logger.warning("Redis set failed: %s", e)
                self._mem[key] = value
        else:
            self._mem[key] = value


cache = Cache(ttl_seconds=settings.cache_ttl_seconds)