import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def ping_redis() -> dict[str, Any]:
    try:
        ok = bool(get_redis().ping())
        return {"status": "ok" if ok else "error"}
    except RedisError as exc:
        logger.error("redis_ping_failed", extra={"error": str(exc)})
        raise ServiceUnavailableError("Redis is unavailable") from exc


def close_redis() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
