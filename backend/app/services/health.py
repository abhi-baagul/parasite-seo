import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceUnavailableError
from app.services.redis import ping_redis

logger = logging.getLogger(__name__)


def check_database(session: Session) -> dict[str, Any]:
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        logger.error("database_health_failed", extra={"error": str(exc)})
        raise ServiceUnavailableError("Database is unavailable") from exc


def check_redis() -> dict[str, Any]:
    return ping_redis()
