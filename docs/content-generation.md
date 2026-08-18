# Content Generation Workflow

## Pipeline

```
Prompt → Analyze → Confirm requirements → Research → Strategy → Outline
→ Approve outline → Generate → SEO check → Quality check → Final review
```

Publishing is out of scope for Phase 3.

## APIs

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/content/analyze-prompt` | Store prompt + structured analysis |
| POST | `/api/v1/content/prompts/{id}/confirm-requirements` | Confirm edits + create draft content |
| POST/GET | `/api/v1/content/{id}/research` | Research brief |
| POST/GET | `/api/v1/content/{id}/strategy` | Strategy |
| POST/GET | `/api/v1/content/{id}/outline` | Outline |
| POST | `/api/v1/content/{id}/outline/approve` | Approve/edit outline |
| POST | `/api/v1/content/generate` | Generate article + version |
| POST | `/api/v1/content/{id}/seo-check` | SEO diagnostic |
| POST | `/api/v1/content/{id}/quality-check` | Quality gate |
| GET | `/api/v1/content/{id}/quality-checks` | Stored checks |
| POST | `/api/v1/content/{id}/optimize` | Suggestions only (no auto-overwrite) |

## Persistence

- Original prompt is immutable.
- Analysis stored in `prompt_analyses`.
- Research / strategy / outline keep versioned rows.
- Generation creates `content_versions` and updates `content_assets`.
- HTML is sanitized before save.

## Duplicate protection

If a `content_generation_jobs` row is already `queued`/`running` for the same stage, the API returns the in-progress status (or `409` for generate) instead of starting a duplicate job.
