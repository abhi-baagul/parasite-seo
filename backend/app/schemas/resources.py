from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl, field_validator

from app.models.enums import (
    CampaignStatus,
    ChannelType,
    ContentStatus,
    ContentType,
    KeywordIntent,
    KeywordType,
    LinkAttribute,
    LinkStatus,
    MediaStatus,
    MediaType,
    ProjectStatus,
    PromptStatus,
    PublishStatus,
)
from app.schemas.common import ORMModel


class ProjectCreate(ORMModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    niche: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=40)
    target_audience: str | None = Field(default=None, max_length=255)
    monetization_model: str | None = Field(default=None, max_length=80)
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    niche: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=40)
    target_audience: str | None = Field(default=None, max_length=255)
    monetization_model: str | None = Field(default=None, max_length=80)
    status: ProjectStatus | None = None


class ProjectRead(ORMModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    niche: str | None
    country: str | None
    language: str | None
    target_audience: str | None
    monetization_model: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    campaign_count: int = 0
    content_count: int = 0


class CampaignCreate(ORMModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: CampaignStatus = CampaignStatus.ACTIVE
    target_country: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=40)
    default_content_type: ContentType = ContentType.ARTICLE
    default_word_count: int = Field(default=1200, ge=100, le=20000)


class CampaignUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: CampaignStatus | None = None
    target_country: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=40)
    default_content_type: ContentType | None = None
    default_word_count: int | None = Field(default=None, ge=100, le=20000)


class CampaignRead(ORMModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    status: str
    target_country: str | None
    language: str | None
    default_content_type: str
    default_word_count: int
    created_at: datetime
    updated_at: datetime


class PromptCreate(ORMModel):
    project_id: UUID
    campaign_id: UUID | None = None
    raw_prompt: str = Field(min_length=1)
    status: PromptStatus = PromptStatus.DRAFT


class PromptRead(ORMModel):
    id: UUID
    project_id: UUID
    campaign_id: UUID | None
    raw_prompt: str
    status: str
    created_at: datetime
    updated_at: datetime


class ContentCreate(ORMModel):
    project_id: UUID
    campaign_id: UUID | None = None
    prompt_id: UUID | None = None
    title: str = Field(min_length=1, max_length=300)
    slug: str = Field(min_length=1, max_length=320)
    content: str = ""
    seo_title: str | None = Field(default=None, max_length=300)
    meta_description: str | None = None
    content_type: ContentType = ContentType.ARTICLE
    status: ContentStatus = ContentStatus.DRAFT
    word_count: int = Field(default=0, ge=0)
    seo_score: int | None = Field(default=None, ge=0, le=100)
    quality_score: int | None = Field(default=None, ge=0, le=100)


class ContentUpdate(ORMModel):
    campaign_id: UUID | None = None
    prompt_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    slug: str | None = Field(default=None, min_length=1, max_length=320)
    content: str | None = None
    seo_title: str | None = Field(default=None, max_length=300)
    meta_description: str | None = None
    content_type: ContentType | None = None
    status: ContentStatus | None = None
    word_count: int | None = Field(default=None, ge=0)
    seo_score: int | None = Field(default=None, ge=0, le=100)
    quality_score: int | None = Field(default=None, ge=0, le=100)


class ContentRead(ORMModel):
    id: UUID
    project_id: UUID
    campaign_id: UUID | None
    prompt_id: UUID | None
    title: str
    slug: str
    content: str
    seo_title: str | None = None
    meta_description: str | None = None
    structured_body: dict | None = None
    content_type: str
    status: str
    word_count: int
    seo_score: int | None
    quality_score: int | None
    created_at: datetime
    updated_at: datetime


class ContentVersionCreate(ORMModel):
    content: str | None = None
    change_summary: str | None = None


class ContentVersionRead(ORMModel):
    id: UUID
    content_asset_id: UUID
    version_number: int
    content: str
    change_summary: str | None
    source: str = "manual"
    created_by: UUID | None
    created_at: datetime


class LinkCreate(ORMModel):
    content_asset_id: UUID
    target_url: str = Field(min_length=1, max_length=2048)
    anchor_text: str = Field(min_length=1, max_length=500)
    placement_description: str | None = None
    link_attribute: LinkAttribute = LinkAttribute.STANDARD
    status: LinkStatus = LinkStatus.PLANNED

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = str(HttpUrl(value))
        return parsed


class LinkUpdate(ORMModel):
    target_url: str | None = Field(default=None, min_length=1, max_length=2048)
    anchor_text: str | None = Field(default=None, min_length=1, max_length=500)
    placement_description: str | None = None
    link_attribute: LinkAttribute | None = None
    status: LinkStatus | None = None

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return str(HttpUrl(value))


class LinkRead(ORMModel):
    id: UUID
    content_asset_id: UUID
    target_url: str
    anchor_text: str
    placement_description: str | None
    link_attribute: str
    status: str
    created_at: datetime
    updated_at: datetime


class MediaCreate(ORMModel):
    project_id: UUID
    content_asset_id: UUID | None = None
    media_type: MediaType = MediaType.GENERATED_IMAGE
    url: str | None = Field(default=None, max_length=2048)
    storage_key: str | None = Field(default=None, max_length=512)
    prompt: str | None = None
    alt_text: str | None = None
    caption: str | None = None
    source: str | None = Field(default=None, max_length=255)
    license_information: str | None = None
    status: MediaStatus = MediaStatus.DRAFT


class MediaUpdate(ORMModel):
    content_asset_id: UUID | None = None
    media_type: MediaType | None = None
    url: str | None = Field(default=None, max_length=2048)
    storage_key: str | None = Field(default=None, max_length=512)
    prompt: str | None = None
    alt_text: str | None = None
    caption: str | None = None
    source: str | None = Field(default=None, max_length=255)
    license_information: str | None = None
    status: MediaStatus | None = None


class MediaRead(ORMModel):
    id: UUID
    project_id: UUID
    content_asset_id: UUID | None
    media_type: str
    url: str | None
    storage_key: str | None
    prompt: str | None
    alt_text: str | None
    caption: str | None
    source: str | None
    license_information: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class PublishingChannelCreate(ORMModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=200)
    channel_type: ChannelType = ChannelType.CUSTOM
    configuration: dict = Field(default_factory=dict)
    is_active: bool = True


class PublishingChannelUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    channel_type: ChannelType | None = None
    configuration: dict | None = None
    is_active: bool | None = None


class PublishingChannelRead(ORMModel):
    id: UUID
    project_id: UUID
    name: str
    channel_type: str
    configuration: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PublishedAssetRead(ORMModel):
    id: UUID
    content_asset_id: UUID
    publishing_channel_id: UUID
    published_url: str | None
    external_id: str | None
    status: str
    published_at: datetime | None
    last_checked_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class AIRunRead(ORMModel):
    id: UUID
    project_id: UUID | None
    content_asset_id: UUID | None
    agent_type: str
    model: str | None
    status: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    execution_time_ms: int | None
    input_summary: str | None
    output_summary: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class KeywordCreate(ORMModel):
    project_id: UUID
    content_asset_id: UUID | None = None
    keyword: str = Field(min_length=1, max_length=255)
    keyword_type: KeywordType = KeywordType.PRIMARY
    search_volume: int | None = Field(default=None, ge=0)
    difficulty: int | None = Field(default=None, ge=0, le=100)
    cpc: float | None = Field(default=None, ge=0)
    intent: KeywordIntent | None = KeywordIntent.INFORMATIONAL
    country: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=40)
    opportunity_score: float | None = None


class KeywordUpdate(ORMModel):
    content_asset_id: UUID | None = None
    keyword: str | None = Field(default=None, min_length=1, max_length=255)
    keyword_type: KeywordType | None = None
    search_volume: int | None = Field(default=None, ge=0)
    difficulty: int | None = Field(default=None, ge=0, le=100)
    cpc: float | None = Field(default=None, ge=0)
    intent: KeywordIntent | None = None
    country: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=40)
    opportunity_score: float | None = None


class KeywordRead(ORMModel):
    id: UUID
    project_id: UUID
    content_asset_id: UUID | None
    keyword: str
    keyword_type: str
    search_volume: int | None
    difficulty: int | None
    cpc: float | None
    intent: str | None
    country: str | None
    language: str | None
    opportunity_score: float | None
    created_at: datetime
    updated_at: datetime


class AnalyticsMetricRead(ORMModel):
    id: UUID
    project_id: UUID
    content_asset_id: UUID | None
    metric_type: str
    metric_value: float
    metric_date: datetime | str
    source: str | None
    created_at: datetime


class AnalyticsOverview(ORMModel):
    impressions: float = 0
    clicks: float = 0
    ctr: float = 0
    traffic: float = 0
    average_position: float = 0
    conversions: float = 0
    revenue: float = 0
    metric_count: int = 0
