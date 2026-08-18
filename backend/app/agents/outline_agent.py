import json

from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.ai_pipeline import ContentOutlineSchema


class OutlineAgent(BaseAgent):
    agent_type = AgentType.OUTLINE
    schema_model = ContentOutlineSchema
    system_prompt = (
        "You are an Outline Agent. Produce H1/H2/H3 outline sections that respect requested structure "
        "(intro, lists, tables, FAQ, conclusion, CTA). Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Produce an outline.\n\n"
            f"REQUIREMENTS:\n{json.dumps(kwargs['requirements'], ensure_ascii=True)}\n\n"
            f"STRATEGY:\n{json.dumps(kwargs['strategy'], ensure_ascii=True)}\n\n"
            "Return JSON: {h1, sections:[{heading, level, purpose, notes}]} "
            "purpose may be introduction|main|list|table|faq|conclusion|cta."
        )
