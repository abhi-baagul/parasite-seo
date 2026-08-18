"""Phase 7 — Link Intelligence Agent for internal content relationships."""

from typing import Any

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.models.enums import AgentType


class LinkSuggestionItem(BaseModel):
    source_title: str
    target_title: str
    anchor_text: str = Field(min_length=2, max_length=120)
    placement: str | None = None
    context: str | None = None
    reason: str
    relevance_score: int = Field(ge=0, le=100)
    confidence_score: int = Field(ge=0, le=100)


class LinkIntelligenceResult(BaseModel):
    suggestions: list[LinkSuggestionItem] = Field(default_factory=list)
    notes: str | None = None


class LinkIntelligenceAgent(BaseAgent):
    agent_type = AgentType.LINK_INTELLIGENCE
    schema_model = LinkIntelligenceResult
    system_prompt = (
        "You are a Link Intelligence Agent for same-domain INTERNAL LINKS only. "
        "Recommend contextual links between related published articles on the same site. "
        "Do not invent pages. Do not treat internal links as backlinks. "
        "Prefer natural varied anchor text. Only suggest genuinely useful relationships. "
        "Skip pairs that are only keyword-overlapping without helpful context. "
        "Flag near-duplicate topics in notes if content appears overlapping."
    )

    def build_user_prompt(self, **kwargs: Any) -> str:
        source = kwargs.get("source") or {}
        candidates = kwargs.get("candidates") or []
        return (
            "Recommend internal links FROM the source page TO candidate pages.\n"
            "Return at most 5 high-quality suggestions.\n\n"
            f"SOURCE:\n{source}\n\n"
            f"CANDIDATES:\n{candidates}\n"
        )
