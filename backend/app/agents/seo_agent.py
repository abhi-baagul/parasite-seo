import json

from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.ai_pipeline import SeoReportSchema


class SeoAgent(BaseAgent):
    agent_type = AgentType.SEO
    schema_model = SeoReportSchema
    system_prompt = (
        "You are an SEO Analysis Agent. Produce an editorial diagnostic report, "
        "not a Google ranking guarantee. Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Run SEO analysis on this article.\n\n"
            f"REQUIREMENTS:\n{json.dumps(kwargs['requirements'], ensure_ascii=True)}\n\n"
            f"TITLE: {kwargs.get('title')}\n"
            f"HTML:\n{kwargs['html'][:20000]}\n\n"
            "Return JSON with overall_score, structure_score, keyword_coverage_score, "
            "readability_score, intent_score, issues, recommendations."
        )
