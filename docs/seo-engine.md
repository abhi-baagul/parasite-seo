# SEO Engine (Phase 4)

## Architecture

```
backend/app/seo/
  analyzer.py      # orchestration
  structure.py
  keywords.py
  metadata.py
  links.py
  readability.py
  scoring.py       # Content SEO Score (editorial)
```

Enrichment service: `backend/app/services/seo_enrichment.py`

AI agents (optional generation):
- `MetadataAgent`
- `TaxonomyAgent`
- `MediaPlanAgent`

## Content SEO Score

Weighted editorial blend of structure, keywords, readability, metadata, links, and media.

**Not** a Google ranking score. APIs and UI label it **Content SEO Score**.

## Caching

SEO and keyword analyses store `content_hash`. Identical body reuses the prior report unless `force=True`.

## Key endpoints

- `POST /api/v1/content/{id}/seo/analyze`
- `GET /api/v1/content/{id}/seo`
- `POST /api/v1/content/{id}/keyword-analysis`
- `POST /api/v1/content/{id}/seo/generate-metadata`
- `POST /api/v1/content/{id}/seo/select-metadata`
- `POST /api/v1/content/{id}/seo/generate-tags`
- `POST /api/v1/content/{id}/seo/generate-media-plan`
- `POST /api/v1/content/{id}/seo/generate-all`
