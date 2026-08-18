# Asset Management (Phase 5)

## Asset Library

`GET /api/v1/assets/library` returns a unified list of:

- Content assets
- Media assets

UI: `/assets` — search, list/grid, open/attach via links.

## Media

Existing Phase 4 media endpoints remain the source of truth for images/videos.
Studio Media panel lists attached assets; insertion into the article uses https URLs / approved embeds.

## Storage

```
StorageProvider
  LocalStorageProvider   ← Phase 5 default (backend/storage)
  S3StorageProvider      ← interface ready, not activated
```

Binary exports are stored by `storage_key` in `content_asset_files` — not as large blobs in PostgreSQL.
