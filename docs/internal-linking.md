# Internal Linking (Phase 7)

## Rules

- Only link **published + public** pages in the **same project**
- Never auto-insert unless Automatic Internal Linking is enabled
- Default minimum relevance: **85**
- Max new links per article / same target / section are configurable
- Insertion creates a `ContentVersion` and re-runs SEO analysis
- Live public pages keep the published snapshot until explicitly updated (Phase 6)

## Anchor text

- Prefer natural, varied anchors
- User can edit before approve
- Anchor diversity is reported in Link Health

## Orphans & broken links

- Orphan = published page with 0 incoming internal links
- Broken = `/p/...` target missing, unpublished, or invalid
- Actions: create suggestion, remove broken link

## Slug changes

Changing a public slug creates a redirect row and updates matching internal `ContentLink` / HTML hrefs.
