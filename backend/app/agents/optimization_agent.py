import json

from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.ai_pipeline import OptimizationReportSchema


class OptimizationAgent(BaseAgent):
    agent_type = AgentType.OPTIMIZATION
    schema_model = OptimizationReportSchema
    system_prompt = (
        "You are an Optimization Agent. Propose optional improvements as before/after/reason. "
        "Do not rewrite the entire article. Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        instructions = kwargs.get("instructions") or "Improve clarity and verification wording."
        return (
            f"Optimize the article with these instructions: {instructions}\n\n"
            f"HTML:\n{kwargs['html'][:20000]}\n\n"
            "Return JSON: {suggestions:[{before, after, reason}]}"
        )
