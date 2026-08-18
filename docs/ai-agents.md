# AI Agents

Each agent lives under `backend/app/agents/` and extends `BaseAgent`.

| Agent | Responsibility | Schema |
| --- | --- | --- |
| Prompt Analyzer | Extract requirements from raw prompt | `PromptAnalysisSchema` |
| Research | Research brief without fabricated sources | `ResearchBriefSchema` |
| Strategy | Editorial strategy (not the article) | `ContentStrategySchema` |
| Outline | H1/H2/H3 outline | `ContentOutlineSchema` |
| Content | Full article HTML + metadata | `GeneratedArticleSchema` |
| SEO | Editorial SEO diagnostic | `SeoReportSchema` |
| Quality | Quality gate | `QualityReportSchema` |
| Optimization | before/after suggestions only | `OptimizationReportSchema` |

## Base behavior

1. Create AI run (`running`)
2. Call provider with system + user prompts
3. Parse JSON and validate against schema
4. On invalid output: one controlled repair retry
5. Persist run as `completed` or `failed`

Agents do not invent verified sources. Unverified promotional claims are flagged for review.
