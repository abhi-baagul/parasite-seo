from enum import StrEnum


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class CampaignStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PromptStatus(StrEnum):
    DRAFT = "draft"
    ANALYZED = "analyzed"
    USED = "used"
    ARCHIVED = "archived"


class ContentType(StrEnum):
    ARTICLE = "article"
    LISTICLE = "listicle"
    COMPARISON = "comparison"
    GUIDE = "guide"
    REVIEW = "review"
    RESOURCE_PAGE = "resource_page"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    STRATEGIZING = "strategizing"
    OUTLINING = "outlining"
    GENERATING = "generating"
    GENERATED = "generated"
    REVIEW = "review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class LinkAttribute(StrEnum):
    STANDARD = "standard"
    SPONSORED = "sponsored"
    UGC = "ugc"
    NOFOLLOW = "nofollow"


class LinkStatus(StrEnum):
    PLANNED = "planned"
    INSERTED = "inserted"
    VERIFIED = "verified"
    BROKEN = "broken"
    REMOVED = "removed"


class MediaType(StrEnum):
    GENERATED_IMAGE = "generated_image"
    UPLOADED_IMAGE = "uploaded_image"
    VIDEO_EMBED = "video_embed"
    IMAGE = "image"
    VIDEO = "video"
    DIAGRAM = "diagram"
    INFOGRAPHIC = "infographic"


class MediaStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    ATTACHED = "attached"
    FAILED = "failed"
    SUGGESTED = "suggested"
    APPROVED = "approved"
    GENERATED = "generated"
    REJECTED = "rejected"


class SuggestionStatus(StrEnum):
    SUGGESTED = "suggested"
    APPROVED = "approved"
    REJECTED = "rejected"
    INSERTED = "inserted"


class ChannelType(StrEnum):
    WORDPRESS = "wordpress"
    GHOST = "ghost"
    WEBFLOW = "webflow"
    CUSTOM = "custom"


class PublishStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class AgentType(StrEnum):
    PROMPT_ANALYZER = "prompt_analyzer"
    RESEARCH = "research"
    STRATEGY = "strategy"
    OUTLINE = "outline"
    CONTENT = "content"
    SECTION_EDIT = "section_edit"
    SEO = "seo"
    MEDIA = "media"
    QUALITY = "quality"
    OPTIMIZATION = "optimization"
    LINK_INTELLIGENCE = "link_intelligence"
    PROJECT_INTELLIGENCE = "project_intelligence"
    CAMPAIGN_STRATEGY = "campaign_strategy"
    PUBLISHING = "publishing"
    MONITORING = "monitoring"
    ANALYTICS = "analytics"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    SUCCESS = "success"  # legacy alias used by Phase 2A seed/tests
    WARNING = "warning"
    FAILED = "failed"
    ERROR = "error"  # legacy alias
    CANCELLED = "cancelled"


class QualityCheckType(StrEnum):
    SEO = "seo"
    QUALITY = "quality"
    KEYWORD_COVERAGE = "keyword_coverage"
    LINKS = "links"
    MEDIA = "media"
    METADATA = "metadata"


class QualityStatus(StrEnum):
    PASSED = "passed"
    NEEDS_REVIEW = "needs_review"
    WARNING = "warning"
    FAILED = "failed"


class KeywordType(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    RELATED = "related"


class KeywordIntent(StrEnum):
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class AnalyticsMetricType(StrEnum):
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CTR = "ctr"
    TRAFFIC = "traffic"
    AVERAGE_POSITION = "average_position"
    CONVERSIONS = "conversions"
    REVENUE = "revenue"
