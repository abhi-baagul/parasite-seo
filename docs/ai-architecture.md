# AI Provider Architecture

Phase 3 uses a provider-independent LLM layer.

```
AIProvider (abstract)
  ├── OpenRouterProvider
  └── MockAIProvider (tests / offline development)
```

## Configuration (backend only)

| Variable | Purpose |
| --- | --- |
| `OPENROUTER_API_KEY` | Provider API key (never sent to the browser) |
| `OPENROUTER_BASE_URL` | OpenRouter-compatible base URL |
| `DEFAULT_AI_MODEL` | Default model id |
| `AI_TEMPERATURE` | Sampling temperature |
| `AI_MAX_TOKENS` | Max completion tokens |
| `AI_TIMEOUT` | Request timeout (seconds) |
| `AI_MAX_RETRIES` | Bounded retries for 429/5xx/timeouts |
| `AI_MAX_GENERATION_CHARS` | Input size safeguard |

Factory: `app.integrations.ai.factory.get_ai_provider()`

- Development/test without a key → `MockAIProvider`
- Configured key → `OpenRouterProvider`

## Design rules

- Route handlers never call OpenRouter directly.
- Agents call `AIProvider.complete(...)`.
- API keys exist only in backend environment variables.
- Structured outputs are validated with Pydantic before persistence.
