import json

from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.ai_pipeline import GeneratedArticleSchema


class ContentAgent(BaseAgent):
    agent_type = AgentType.CONTENT
    schema_model = GeneratedArticleSchema
    system_prompt = (
        "You are a Content Agent. Write a complete useful article from the approved outline. "
        "Prioritize accuracy, readability, and clear structure. Do not keyword-stuff. "
        "Do not invent verified sources. Label promotional claims as requiring verification. "
        "Do not claim ranking or indexing guarantees. "
        "Return ONLY JSON with title, seo_title, meta_description, slug, h1, html, word_count. "
        "html may include h1-h3, p, ul/ol, table, and a CTA div with class cta-block. "
        "Use media placeholders as italic notes, not real images."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Generate the article.\n\n"
            f"ORIGINAL PROMPT:\n{kwargs['raw_prompt']}\n\n"
            f"REQUIREMENTS:\n{json.dumps(kwargs['requirements'], ensure_ascii=True)}\n\n"
            f"RESEARCH:\n{json.dumps(kwargs['research'], ensure_ascii=True)}\n\n"
            f"STRATEGY:\n{json.dumps(kwargs['strategy'], ensure_ascii=True)}\n\n"
            f"APPROVED OUTLINE:\n{json.dumps(kwargs['outline'], ensure_ascii=True)}\n"
        )
