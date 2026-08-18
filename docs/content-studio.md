# Content Studio (Phase 5)

## Architecture

Content Studio is the professional editing workspace for generated articles.

```
Frontend (Next.js)
  StudioWorkspace
    → GET /api/v1/content/{id}/studio   (aggregate payload)
    → PATCH /api/v1/content/{id}        (autosave / draft)
    → versions / AI section-edit / export / duplicate
Backend (FastAPI)
  content_studio service
  export service
  LocalStorageProvider (S3-ready interface)
```

Layout:

- Top bar: back, title, status, save state, Preview / Export / Approve
- Left: document outline + completeness
- Center: rich editor + AI section actions + word count
- Right: SEO / Quality / Links / Media / Metadata / AI / References / Versions

## Editor

`contentEditable` rich editor with semantic commands:

H1–H3, paragraphs, bold/italic/underline, lists, blockquote, tables, links, images, video embeds (YouTube/Vimeo only), CTA blocks, HR.

HTML is sanitized server-side (`bleach`) before save/export.

## Autosave

Dirty detection + 1.6s debounce updates the live draft via PATCH.  
**Save version** creates a `ContentVersion` explicitly.

## Preview

Reader preview modes: desktop / tablet / mobile. No editor chrome.

## Security

- Ownership checks on all studio endpoints
- XSS stripped on save
- `javascript:` URLs rejected
- Publish/schedule status blocked in Phase 5
- Export downloads do not expose filesystem paths
