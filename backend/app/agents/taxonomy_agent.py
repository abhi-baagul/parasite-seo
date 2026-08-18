from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.seo_enrichment import TagsCategoriesSchema


class TaxonomyAgent(BaseAgent):
    agent_type = AgentType.SEO
    schema_model = TagsCategoriesSchema
    system_prompt = (
        "You are a Taxonomy Agent. Generate a small set of relevant tags and categories. "
        "Avoid duplicates and overly broad junk tags. Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Generate tags and categories for this article.\n"
            f"TOPIC: {kwargs.get('topic')}\n"
            f"KEYWORDS: {kwargs.get('keywords')}\n"
            f"HTML:\n{(kwargs.get('html') or '')[:8000]}\n"
            "Return JSON {tags:[...], categories:[...]} with at most 8 tags and 4 categories."
        )
