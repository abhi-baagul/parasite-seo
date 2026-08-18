from app.agents.base import BaseAgent
from app.models.enums import AgentType
from app.schemas.ai_pipeline import PromptAnalysisSchema


class PromptAnalyzerAgent(BaseAgent):
    agent_type = AgentType.PROMPT_ANALYZER
    schema_model = PromptAnalysisSchema
    system_prompt = (
        "You are a Prompt Analyzer for SEO content operations. "
        "Extract structured requirements from the user's original prompt. "
        "Do not invent missing information. If unsure, use null and list the field in uncertain_fields. "
        "cta_requirement must be true, false, or null — never a sentence. "
        "List fields must be JSON arrays (use [] when unknown), never null. "
        "Return ONLY valid JSON matching the schema."
    )

    def build_user_prompt(self, **kwargs) -> str:
        raw_prompt = kwargs["raw_prompt"]
        return (
            "Extract structured SEO content requirements from this prompt. "
            "Preserve promotional codes and quotes exactly when present.\n\n"
            f"PROMPT:\n{raw_prompt}\n\n"
            "JSON keys: topic, main_keyword, secondary_keywords, word_count, content_type, intent, "
            "tone, audience, country, language, required_headings, required_elements, cta_requirement, "
            "offer_information, promotional_information, target_url_if_present, anchor_text_if_present, "
            "media_requirements, special_instructions, uncertain_fields."
        )
