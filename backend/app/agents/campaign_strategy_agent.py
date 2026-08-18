import json

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.models.enums import AgentType


class CampaignStrategySchema(BaseModel):
    strategy_type: str
    label: str | None = None
    reason: str | None = None
    blueprint: dict = Field(default_factory=dict)


class CampaignStrategyAgent(BaseAgent):
    agent_type = AgentType.CAMPAIGN_STRATEGY
    schema_model = CampaignStrategySchema
    system_prompt = (
        "You are a Campaign Strategy Agent. Recommend a small authorized campaign structure. "
        "Never recommend mass spam, unauthorized posting, or thousands of pages. Return ONLY JSON."
    )

    def build_user_prompt(self, **kwargs) -> str:
        return (
            "Recommend a campaign strategy.\n\n"
            f"INTELLIGENCE:\n{json.dumps(kwargs.get('intelligence') or {}, ensure_ascii=True)}\n\n"
            f"DESTINATIONS:\n{json.dumps(kwargs.get('destinations') or [], ensure_ascii=True)}\n\n"
            "strategy_type must be one of: single_asset, multi_asset, tiered_network, cloud_network, "
            "digital_pr, authorized_outreach, hybrid. Include blueprint keys tier1, tier2, cloud, pr, outreach, "
            "max_tier_depth. Keep caps small (tier1<=8, tier2<=16, cloud<=5, pr<=2, outreach<=20)."
        )
