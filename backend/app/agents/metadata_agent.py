from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.seo_enrichment import MetadataPackageSchema


class MetadataAgent(BaseAgent):
    agent_type = AgentType.SEO
    schema_model = MetadataPackageSchema
    system_prompt = (
        "You are an SEO Metadata Agent. Generate multiple SEO title and meta description options. "
        "Do not claim ranking guarantees. Return ONLY JSON matching the schema."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Generate SEO metadata options.\n"
            f"TOPIC: {kwargs.get('topic')}\n"
            f"PRIMARY KEYWORD: {kwargs.get('primary_keyword')}\n"
            f"INTENT: {kwargs.get('intent')}\n"
            f"AUDIENCE: {kwargs.get('audience')}\n"
            f"TITLE: {kwargs.get('title')}\n"
            f"HTML:\n{(kwargs.get('html') or '')[:12000]}\n"
            "Return JSON with title_options[{title, character_count, keyword_position, clarity_score, intent_match}], "
            "meta_options[{meta_description, character_count, primary_keyword_present, cta_presence}], "
            "slug, og_title, og_description, twitter_title, twitter_description."
        )
