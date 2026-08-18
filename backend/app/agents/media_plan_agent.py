from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.seo_enrichment import MediaPlanSchema


class MediaPlanAgent(BaseAgent):
    agent_type = AgentType.MEDIA
    schema_model = MediaPlanSchema
    system_prompt = (
        "You are a Media Planning Agent. Suggest only media that genuinely improves understanding. "
        "Include image prompts and alt text that are descriptive, not keyword-stuffed. "
        "Do not invent copyrighted video URLs. Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Create a media plan for this article.\n"
            f"TOPIC: {kwargs.get('topic')}\n"
            f"HTML:\n{(kwargs.get('html') or '')[:10000]}\n"
            "Return JSON with items[{media_type, placement, purpose, description, generation_prompt, alt_text, caption, suggested_filename}] "
            "and video_suggestions with the same fields (no fabricated embed URLs)."
        )
