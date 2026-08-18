# Content Network (Phase 7)

Same-domain **internal links** between published Parasite SEO public pages.

## Concepts

| Term | Meaning |
| --- | --- |
| Internal link | Same-domain `/p/{slug}` → `/p/{slug}` |
| Backlink | Link from another website to yours |
| External link | Link from your page to another website |
| Target link | User-provided commercial destination |

## Flow

```
Published pages → Analyze network → Suggestions → Approve → Insert + version + SEO recheck
```

Automatic internal linking is **OFF** by default.

## APIs

- `POST /api/v1/parasite-seo/link-network/analyze`
- `GET /api/v1/parasite-seo/link-network?project_id=`
- `GET /api/v1/parasite-seo/link-suggestions`
- `POST /api/v1/parasite-seo/link-suggestions/{id}/approve|reject`
- Settings + orphan opportunities + slug redirect apply

## UI

Parasite SEO AI → **Content network** (`/parasite-seo/network`)

Tabs: Overview, Suggestions, Orphans, Broken, Graph, Health

Content Studio → **Internal** panel for per-article suggestions.
