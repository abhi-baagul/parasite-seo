import json

from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.ai_pipeline import ResearchBriefSchema


class ResearchAgent(BaseAgent):
    agent_type = AgentType.RESEARCH
    schema_model = ResearchBriefSchema
    system_prompt = (
        "You are a Research Agent. Produce a research brief without fabricating sources or facts. "
        "If you lack verified sources, leave sources empty and list claims_requiring_verification. "
        "Never pretend that live web research occurred. Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        requirements = kwargs["requirements"]
        return (
            "Create a research brief from these confirmed requirements. "
            "Mark unverified promotional claims clearly.\n\n"
            f"REQUIREMENTS:\n{json.dumps(requirements, ensure_ascii=True)}\n\n"
            "Return JSON with topic_summary, key_facts, entities, questions, subtopics, "
            "supporting_information, sources, claims_requiring_verification."
        )
