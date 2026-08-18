import json
import logging
import sys
from typing import Any

from app.core.config import settings

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "secret",
    "jwt_secret",
    "aws_secret_access_key",
    "openrouter_api_key",
    "seo_provider_api_key",
    "credentials",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "request_id",
            "method",
            "route",
            "status",
            "execution_time_ms",
            "error",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info and not settings.is_production:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO if settings.is_production else logging.DEBUG)
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("redis.connection").setLevel(logging.WARNING)


def redact(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        lowered = key.lower()
        if any(part in lowered for part in SENSITIVE_KEYS):
            cleaned[key] = "[redacted]"
        else:
            cleaned[key] = value
    return cleaned
