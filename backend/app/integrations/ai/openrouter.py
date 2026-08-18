import logging
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import RateLimitError, ServiceUnavailableError
from app.integrations.ai.base import AICompletionResult, AIMessage, AIProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(AIProvider):
    name = "openrouter"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openrouter_api_key
        self.base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self.default_model = default_model or settings.default_ai_model
        self.timeout = timeout if timeout is not None else settings.ai_timeout
        self.max_retries = max_retries if max_retries is not None else settings.ai_max_retries
        if not self.api_key:
            raise ServiceUnavailableError(
                "OPENROUTER_API_KEY is not configured. Add it to the backend environment."
            )

    def complete(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format_json: bool = True,
    ) -> AICompletionResult:
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": settings.ai_temperature if temperature is None else temperature,
            "max_tokens": settings.ai_max_tokens if max_tokens is None else max_tokens,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://parasiteseo.local",
            "X-Title": "Parasite SEO AI Automation",
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                if response.status_code == 429:
                    raise RateLimitError("AI provider rate limited the request")
                if response.status_code >= 500:
                    raise ServiceUnavailableError("AI provider returned a server error")
                if response.status_code >= 400:
                    # Do not leak API key or full upstream body in production messages.
                    raise ServiceUnavailableError(
                        f"AI provider rejected the request (HTTP {response.status_code})"
                    )
                data = response.json()
                choice = (data.get("choices") or [{}])[0]
# Normalize OpenRouter content that may arrive as multimodal parts.
                message = choice.get("message") or {}
                content = message.get("content") or ""
                if isinstance(content, list):
                    parts: list[str] = []
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            parts.append(str(part.get("text") or ""))
                        elif isinstance(part, str):
                            parts.append(part)
                    content = "".join(parts)
                usage = data.get("usage") or {}
                input_tokens = int(usage.get("prompt_tokens") or 0)
                output_tokens = int(usage.get("completion_tokens") or 0)
                return AICompletionResult(
                    content=content,
                    model=str(data.get("model") or payload["model"]),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=int(usage.get("total_tokens") or (input_tokens + output_tokens)),
                    raw={"id": data.get("id"), "usage": usage},
                )
            except (RateLimitError, ServiceUnavailableError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
                time.sleep(min(2**attempt, 8))
            except httpx.TimeoutException as exc:
                last_error = ServiceUnavailableError("AI provider request timed out")
                if attempt >= self.max_retries:
                    raise last_error from exc
                time.sleep(min(2**attempt, 8))
            except httpx.HTTPError as exc:
                last_error = ServiceUnavailableError("AI provider is unavailable")
                logger.warning("openrouter_http_error", extra={"error": type(exc).__name__})
                if attempt >= self.max_retries:
                    raise last_error from exc
                time.sleep(min(2**attempt, 8))
        raise last_error or ServiceUnavailableError("AI provider failed")
