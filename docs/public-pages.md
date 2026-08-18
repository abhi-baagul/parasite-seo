"""Docs: Phase 6 public web page + permanent URL engine."""

# Phase 6 — Public Web Page + Permanent URL Engine

Turns approved Parasite SEO content into a real public article at `/p/{slug}`.

## Flow

```
Approved content → Create web page → Slug → Preview → Make public → /p/{slug}
```

## Model

`PublicPage` (`public_pages` table) — one page per Parasite SEO job.

Statuses: `draft | building | ready | published | unpublished | archived | failed`  
Visibility: `private | public`

Publishing snapshots a `ContentVersion` into `published_version_id` so later edits do not auto-update the live page.

## URLs

Configured via `PUBLIC_APP_URL` (fallback: first `CORS_ORIGINS` entry).

Example: `http://localhost:3000/p/diclock-referral-code-2026`

## APIs

| Method | Path | Auth |
| --- | --- | --- |
| POST | `/api/v1/parasite-seo/jobs/{id}/web-page` | yes |
| GET | `/api/v1/parasite-seo/jobs/{id}/web-page?preview=true` | yes |
| PATCH | `/api/v1/parasite-seo/jobs/{id}/web-page` | yes |
| POST | `/api/v1/parasite-seo/jobs/{id}/web-page/publish` | yes |
| POST | `/api/v1/parasite-seo/jobs/{id}/web-page/unpublish` | yes |
| POST | `/api/v1/parasite-seo/jobs/{id}/web-page/archive` | yes |
| POST | `/api/v1/parasite-seo/jobs/{id}/web-page/update-published` | yes |
| DELETE | `/api/v1/parasite-seo/jobs/{id}/web-page` | yes |
| GET | `/api/v1/public-pages/{slug}` | public |
| GET | `/api/v1/parasite-seo/public/pages/{slug}` | public (legacy) |

## Security

- HTML sanitized with bleach before render
- Unsafe URL schemes rejected
- Public payload excludes prompts, AI runs, and private project data
- Unpublished / private / archived pages return 404
