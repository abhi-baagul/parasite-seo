import json

from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.ai_pipeline import QualityReportSchema


class QualityAgent(BaseAgent):
    agent_type = AgentType.QUALITY
    schema_model = QualityReportSchema
    system_prompt = (
        "You are a Quality Agent. Check missing sections, unsupported claims, repetition, "
        "requested elements, CTA, tables/bullets, and promotional overclaiming. "
        "status must be passed|needs_review|failed. Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Perform a quality review.\n\n"
            f"REQUIREMENTS:\n{json.dumps(kwargs['requirements'], ensure_ascii=True)}\n\n"
            f"HTML:\n{kwargs['html'][:20000]}\n"
        )
