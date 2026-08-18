import json

from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.ai_pipeline import ContentStrategySchema


class StrategyAgent(BaseAgent):
    agent_type = AgentType.STRATEGY
    schema_model = ContentStrategySchema
    system_prompt = (
        "You are a Content Strategy Agent. Create an editorial strategy from requirements and research. "
        "Do not write the final article. Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Create a content strategy.\n\n"
            f"REQUIREMENTS:\n{json.dumps(kwargs['requirements'], ensure_ascii=True)}\n\n"
            f"RESEARCH:\n{json.dumps(kwargs['research'], ensure_ascii=True)}\n\n"
            "Return JSON with content_angle, search_intent, target_audience, content_goals, "
            "recommended_structure, key_topics, differentiation_opportunities, cta_strategy, "
            "internal_link_opportunities, external_reference_opportunities, media_opportunities."
        )
