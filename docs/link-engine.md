# Link Engine (Phase 4)

## Capabilities

- Target link planning with attribute (`standard` / `sponsored` / `ugc` / `nofollow`)
- Contextual placement suggestion (review before insert)
- Internal link suggestions from same-project content (heuristic overlap)
- External reference placeholders marked `requires_verification` (no fabricated URLs)
- Safe URL validation (`https` required by default; `ALLOW_HTTP_LINKS` optional)

## Rejected schemes

`javascript:`, `data:`, `file:`, and other unsafe schemes are rejected.

## Endpoints

- CRUD: `/api/v1/links`
- `POST /api/v1/content/{id}/links/analyze`
- `POST /api/v1/content/{id}/links/suggest`
- `POST /api/v1/content/{id}/links/insert` (creates ContentVersion)
- Internal: `/api/v1/content/{id}/internal-link-suggestions`
- External: `/api/v1/content/{id}/external-references`

## Attributes (UI copy)

- **Sponsored** — paid/sponsored placements
- **UGC** — user-generated content links
- **Nofollow** — signal that the link should not pass ranking credit

Do not choose a deceptive attribute automatically.

## Phase 7

Project-wide content network and internal-link automation live under Parasite SEO AI:

- Docs: `docs/content-network.md`, `docs/internal-linking.md`, `docs/link-intelligence.md`
- UI: `/parasite-seo/network`
