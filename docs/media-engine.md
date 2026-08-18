# Media Engine (Phase 4)

## Media plan

`MediaPlanAgent` proposes image/diagram/infographic/video opportunities with:

- placement, purpose, description
- generation_prompt
- alt_text / optional caption
- suggested_filename
- status: suggested → approved / rejected

Approved suggestions can create `MediaAsset` library rows (metadata only; no pixel generation yet).

## Video

- Suggestions only; no copyrighted scraping
- Embeds limited to YouTube / Vimeo hosts when a URL is provided
- Validation via `validate_video_embed_url`

## Endpoints

- `POST /api/v1/content/{id}/seo/generate-media-plan`
- `POST /api/v1/content/{id}/media/video-suggestions`
- `GET /api/v1/content/{id}/media`
- CRUD: `/api/v1/media` (filters: project, content, media_type)

## Out of scope

Actual image-provider generation, publishing, and bulk campaigns land in later phases.
