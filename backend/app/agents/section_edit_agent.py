"""Section-level AI editing agent (selected HTML only)."""

from app.models.enums import AgentType
from app.agents.base import BaseAgent
from pydantic import BaseModel, Field


class SectionEditResult(BaseModel):
    html: str = Field(min_length=1)
    notes: str | None = None


class SectionEditAgent(BaseAgent):
    agent_type = AgentType.SECTION_EDIT
    schema_model = SectionEditResult
    system_prompt = (
        "You are a precise editorial assistant. Rewrite ONLY the provided HTML fragment "
        "according to the action. Preserve semantic tags (p, h2, h3, ul, ol, li, table, a, strong, em). "
        "Do not invent URLs, affiliate claims, or sources. Do not wrap the whole document — return the fragment only."
    )

    def build_user_prompt(self, **kwargs) -> str:  # noqa: ANN003
        action = kwargs.get("action", "improve")
        selected = kwargs.get("selected_html", "")
        tone = kwargs.get("tone")
        instruction = kwargs.get("instruction")
        parts = [
            f"Action: {action}",
            f"Selected HTML:\n{selected}",
        ]
        if tone:
            parts.append(f"Target tone: {tone}")
        if instruction:
            parts.append(f"Extra instruction: {instruction}")
        parts.append('Return JSON: {"html": "...", "notes": "optional"}')
        return "\n\n".join(parts)
