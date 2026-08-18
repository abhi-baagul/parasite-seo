# Backlink Campaigns (Phase 8)

Backlink campaigns live **inside Parasite SEO AI** — not a separate app.

Automatic flow:

```
Dashboard → Project → Parasite SEO AI → prompt → media → generate → public URL
  → [Create backlink campaign]
  → Project Intelligence Agent → strategy → diagram → assets
  → Review / Approve / Customize
  → Mock or authorized publish → verify → project backlinks → report
```

The user does not have to design tiers, anchors, or topics by hand. Defaults are generated; Customize remains available.

## Terminology

| Term | Meaning |
|------|---------|
| Target / money page | Page you want to promote (auto-selected from the project's published public page) |
| Internal link | Same host `/p/a` → `/p/b` — not counted as a backlink |
| Backlink | External/authorized source linking to the target **and verified** |
| MOCK DATA | Mock-mode publications (`https://mock-source-NNN.local/...`) — never mixed into “real” verified claims for live sites |
| Indexed | Tracked separately as `unknown` unless an authorized index source confirms it |

## Agents

- Project Intelligence Agent — topic, keywords, audience, supporting topics, anchors
- Campaign Strategy Agent — single / multi / tiered / cloud / PR / outreach / hybrid

Blueprints are **planning caps** (hard-limited server-side). They do not mass-create spam pages.

## Publishing

Authorized adapters: `mock_local`, `cloud_static`, `aws_s3`, `gcs`, `azure_blob`, `wordpress` (stub), `generic_cms` (stub).

WordPress/CMS refuse publish without connected credentials. Credentials never return to the frontend.

## Verification

`planned` → `publishing` → `published` → `verified` | `lost` | `broken`

Verified only when source HTML is reachable and the target href is present. Publication success alone is not a backlink.

## API

Prefix: `/api/v1/parasite-seo/backlink-campaigns`

- `GET /analyze` — project intelligence + recommended strategy
- `POST /auto` — create campaign from the project (optional `job_id`)
- `POST /{id}/approve`, `/start`, `/retry-failed`, `/duplicate`, `/archive`
- `GET /{id}/logs`
- `GET /project-backlinks`, `/project-report`
- Existing generate / publish / verify / report endpoints

## Disclosure

> Link acquisition and SEO metrics are informational. Search engines independently determine crawling, indexing, ranking, and link treatment.
