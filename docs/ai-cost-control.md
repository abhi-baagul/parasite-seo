# AI Cost Control

## Tracked per AI run

- agent_type
- model
- status (`queued` / `running` / `completed` / `failed` / `cancelled`)
- input_tokens / output_tokens / total_tokens
- estimated_cost
- execution_time_ms
- started_at / completed_at
- error_message (truncated)
- input/output summaries (not full prompts)

## Safeguards

- `AI_MAX_TOKENS` caps completion size
- `AI_MAX_RETRIES` bounds provider retries
- `AI_TIMEOUT` aborts slow calls
- `AI_MAX_GENERATION_CHARS` rejects oversized inputs
- Generated HTML length is capped before persistence
- Duplicate generation jobs are blocked

## Retries

Provider layer retries transient failures (429, 5xx, timeouts) up to `AI_MAX_RETRIES`.

Agent layer performs at most one structured-output repair retry.

Failures surface to the user with reason + retry option. Fake content is never invented on failure.
