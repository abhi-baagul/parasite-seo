# Versioning (Phase 5)

Uses existing `content_versions` table with added `source` field:

- `manual` — explicit Save version
- `ai` — accepted AI section edit
- `restore` — restore creates a **new** version; history is never deleted

## Restore flow

1. Snapshot current live body (new version)
2. Apply restored body to live content
3. Create another version tagged `restore`

## Compare

`POST /api/v1/content/{id}/versions/compare` returns unified diff + similarity ratio.
