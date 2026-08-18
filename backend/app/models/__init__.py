from app.models.ai_run import AIRun
from app.models.analytics import AnalyticsMetric
from app.models.asset_file import ContentAssetFile
from app.models.backlink_campaign import (
    Backlink,
    BacklinkCampaign,
    BacklinkCheck,
    CampaignAsset,
    CampaignJob,
    CampaignLog,
    CampaignMediaUsage,
    CampaignStrategyTemplate,
    CampaignTask,
    ContentBucket,
    OutreachActivity,
    OutreachProspect,
    PublishingDestination,
)
from app.models.campaign import Campaign
from app.models.content import ContentAsset, ContentLink, ContentVersion
from app.models.content_network import ContentNetworkRun, PublicSlugRedirect
from app.models.keyword import Keyword
from app.models.media import MediaAsset
from app.models.parasite_seo import ParasiteSEOJob
from app.models.public_page import PublicPage
from app.models.pipeline import (
    ContentGenerationJob,
    ContentOutline,
    ContentResearchBrief,
    ContentStrategy,
    PromptAnalysis,
)
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.publishing import PublishedAsset, PublishingChannel
from app.models.quality import QualityCheck
from app.models.seo_enrichment import (
    ContentCategory,
    ContentMetadata,
    ContentTag,
    ExternalReference,
    InternalLinkSuggestion,
    KeywordAnalysisRecord,
    MediaSuggestion,
    SEOAnalysisRecord,
)
from app.models.user import User

__all__ = [
    "AIRun",
    "AnalyticsMetric",
    "Backlink",
    "BacklinkCampaign",
    "BacklinkCheck",
    "Campaign",
    "CampaignAsset",
    "CampaignJob",
    "CampaignLog",
    "CampaignMediaUsage",
    "CampaignStrategyTemplate",
    "CampaignTask",
    "ContentAsset",
    "ContentAssetFile",
    "ContentBucket",
    "ContentCategory",
    "ContentGenerationJob",
    "ContentLink",
    "ContentMetadata",
    "ContentNetworkRun",
    "ContentOutline",
    "ContentResearchBrief",
    "ContentStrategy",
    "ContentTag",
    "ContentVersion",
    "ExternalReference",
    "InternalLinkSuggestion",
    "Keyword",
    "KeywordAnalysisRecord",
    "MediaAsset",
    "MediaSuggestion",
    "OutreachActivity",
    "OutreachProspect",
    "ParasiteSEOJob",
    "PublicPage",
    "PublicSlugRedirect",
    "Project",
    "Prompt",
    "PromptAnalysis",
    "PublishedAsset",
    "PublishingChannel",
    "PublishingDestination",
    "QualityCheck",
    "SEOAnalysisRecord",
    "User",
]


def load_models() -> None:
    """Import all models so Alembic and metadata see every table."""
    return None
