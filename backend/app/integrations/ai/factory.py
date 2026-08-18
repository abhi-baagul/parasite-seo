from functools import lru_cache

from app.core.config import settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.mock import MockAIProvider
from app.integrations.ai.openrouter import OpenRouterProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    """Return the configured provider. Tests may override via dependency injection."""
    if settings.environment == "test" or not settings.openrouter_api_key:
        if settings.environment == "test" or settings.environment == "development":
            # Development without a key uses the mock provider so the UI can be exercised.
            # Production without a key fails when OpenRouterProvider is constructed.
            if not settings.openrouter_api_key:
                return MockAIProvider()
    return OpenRouterProvider()


def reset_ai_provider_cache() -> None:
    get_ai_provider.cache_clear()
