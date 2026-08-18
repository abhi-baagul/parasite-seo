# Export System (Phase 5)

## Endpoints

- `GET /api/v1/content/{id}/export/html`
- `GET /api/v1/content/{id}/export/markdown`
- `GET /api/v1/content/{id}/export/txt`
- `GET /api/v1/content/{id}/export/pdf`

Each response is a file download (`Content-Disposition: attachment`) with a sanitized filename like `diclock-referral-code.html`.

## Formats

| Format | Notes |
|--------|--------|
| HTML | Semantic document wrapper + sanitized body |
| Markdown | `markdownify` conversion |
| TXT | Plain text via BeautifulSoup |
| PDF | `fpdf2` — headings/paragraphs; http(s) links clickable where supported |

Exports register a `content_asset_files` row with storage key for audit — path is never returned to the client.
