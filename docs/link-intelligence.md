# Link Intelligence (Phase 7)

## Agent

`LinkIntelligenceAgent` (`agent_type=link_intelligence`)

Inputs: source page metadata + filtered candidate pages  
Outputs: anchor, placement, reason, relevance, confidence

## Candidate filtering

Before any AI call:

1. Load published public pages in the project
2. Tokenize titles/tags/excerpts
3. Jaccard similarity filter
4. Keep top candidates per source (≤8)
5. Optional AI enrichment; heuristic fallback always available

## Performance

- No N×N AI calls
- Heuristic-only mode: `use_ai=false`
- Analysis run stored in `content_network_runs`

## Security

- Cross-project links blocked
- Private/draft pages excluded from public linking
- HTML sanitized on insert
- Unsafe URL schemes rejected
