import json

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.models.enums import AgentType


class ProjectIntelligenceSchema(BaseModel):
    topic: str | None = None
    primary_keyword: str | None = None
    secondary_keywords: list[str] = Field(default_factory=list)
    search_intent: str | None = None
    content_category: str | None = None
    audience: str | None = None
    recommended_anchor_terms: list[str] = Field(default_factory=list)
    supporting_topics: list[str] = Field(default_factory=list)
    recommended_content_types: list[str] = Field(default_factory=list)
    campaign_strategy: str | None = None
    entities: list[str] = Field(default_factory=list)
    country: str | None = None
    language: str | None = None


class ProjectIntelligenceAgent(BaseAgent):
    agent_type = AgentType.PROJECT_INTELLIGENCE
    schema_model = ProjectIntelligenceSchema
    system_prompt = (
        "You are a Project Intelligence Agent for authorized SEO campaigns. "
        "Analyze the project brief and published page. Do not invent sources, images, or ranking claims. "
        "Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Analyze this project for an authorized backlink campaign.\n\n"
            f"CONTEXT:\n{json.dumps(kwargs.get('context') or {}, ensure_ascii=True)}\n\n"
            "Return topic, primary_keyword, secondary_keywords, search_intent, content_category, audience, "
            "recommended_anchor_terms, supporting_topics, recommended_content_types, campaign_strategy, entities, "
            "country, language."
        )
