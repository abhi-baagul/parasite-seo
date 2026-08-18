"""Phase 8 — Backlink campaign builder models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.content import ContentAsset
    from app.models.project import Project
    from app.models.public_page import PublicPage
    from app.models.publishing import PublishingChannel
    from app.models.user import User


class ContentBucket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_buckets"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    niche: Mapped[str | None] = mapped_column(String(120))
    topics: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(Text)

    project: Mapped["Project"] = relationship()


class CampaignStrategyTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_strategy_templates"

    project_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    strategy_type: Mapped[str] = mapped_column(String(40), nullable=False, default="tiered_network")
    blueprint: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class BacklinkCampaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "backlink_campaigns"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    parasite_job_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("parasite_seo_jobs.id", ondelete="SET NULL"), index=True
    )
    duplicated_from_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlink_campaigns.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    strategy_type: Mapped[str] = mapped_column(String(40), nullable=False, default="tiered_network")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    wizard_step: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    target_url: Mapped[str | None] = mapped_column(String(2048))
    target_content_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("content_assets.id", ondelete="SET NULL"), index=True
    )
    target_public_page_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("public_pages.id", ondelete="SET NULL"), index=True
    )
    primary_keyword: Mapped[str | None] = mapped_column(String(300))
    secondary_keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    country: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str | None] = mapped_column(String(40))
    niche: Mapped[str | None] = mapped_column(String(120))
    target_audience: Mapped[str | None] = mapped_column(String(255))
    blueprint: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    disclosure: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=(
            "Link acquisition and SEO metrics are informational. "
            "Search engines independently determine crawling, indexing, ranking, and link treatment."
        ),
    )
    bucket_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("content_buckets.id", ondelete="SET NULL")
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mock_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    intelligence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    project: Mapped["Project"] = relationship()
    user: Mapped["User"] = relationship()
    target_content: Mapped["ContentAsset | None"] = relationship(foreign_keys=[target_content_id])
    target_page: Mapped["PublicPage | None"] = relationship(foreign_keys=[target_public_page_id])
    bucket: Mapped["ContentBucket | None"] = relationship()
    assets: Mapped[list["CampaignAsset"]] = relationship(back_populates="campaign")
    backlinks: Mapped[list["Backlink"]] = relationship(back_populates="campaign")
    prospects: Mapped[list["OutreachProspect"]] = relationship(back_populates="campaign")
    logs: Mapped[list["CampaignLog"]] = relationship(back_populates="campaign")
    tasks: Mapped[list["CampaignTask"]] = relationship(back_populates="campaign")


class CampaignAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_assets"

    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("content_assets.id", ondelete="SET NULL"), index=True
    )
    master_content_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("content_assets.id", ondelete="SET NULL"), index=True
    )
    destination_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("publishing_destinations.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(40), nullable=False, default="tier1")
    link_group: Mapped[str | None] = mapped_column(String(80))
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    topic: Mapped[str | None] = mapped_column(String(300))
    variant_angle: Mapped[str | None] = mapped_column(String(300))
    relevance_score: Mapped[int | None] = mapped_column(Integer)
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned", index=True)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    target_url: Mapped[str | None] = mapped_column(String(2048))
    parent_asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("campaign_assets.id", ondelete="SET NULL"), index=True
    )
    anchor_text: Mapped[str | None] = mapped_column(String(500))
    link_attribute: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    placement: Mapped[str | None] = mapped_column(String(300))
    quality_score: Mapped[int | None] = mapped_column(Integer)
    seo_score: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    campaign: Mapped["BacklinkCampaign"] = relationship(back_populates="assets")
    content: Mapped["ContentAsset | None"] = relationship(foreign_keys=[content_id])
    destination: Mapped["PublishingDestination | None"] = relationship()


class PublishingDestination(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publishing_destinations"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(40), nullable=False, default="mock_local")
    base_url: Mapped[str | None] = mapped_column(String(2048))
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Encrypted/opaque secrets stay server-side only — never returned to frontend.
    credentials_ref: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    authorization_status: Mapped[str] = mapped_column(String(40), nullable=False, default="authorized")
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    test_status: Mapped[str | None] = mapped_column(String(40))

    project: Mapped["Project"] = relationship()


class Backlink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "backlinks"
    __table_args__ = (
        UniqueConstraint("campaign_id", "source_url", "target_url", "anchor_text", name="uq_backlinks_campaign_triple"),
    )

    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("campaign_assets.id", ondelete="SET NULL"), index=True
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    target_content_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("content_assets.id", ondelete="SET NULL"), index=True
    )
    anchor_text: Mapped[str] = mapped_column(String(500), nullable=False)
    attribute: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="cms")
    link_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="external")
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    indexed_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned", index=True)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    campaign: Mapped["BacklinkCampaign"] = relationship(back_populates="backlinks")
    asset: Mapped["CampaignAsset | None"] = relationship()
    checks: Mapped[list["BacklinkCheck"]] = relationship(back_populates="backlink")


class BacklinkCheck(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "backlink_checks"

    backlink_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlinks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    target_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anchor_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attribute_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    http_status: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    backlink: Mapped["Backlink"] = relationship(back_populates="checks")


class OutreachProspect(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outreach_prospects"

    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    website: Mapped[str] = mapped_column(String(2048), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    topic: Mapped[str | None] = mapped_column(String(300))
    relevance_score: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="prospect", index=True)
    draft_subject: Mapped[str | None] = mapped_column(String(500))
    draft_body: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    campaign: Mapped["BacklinkCampaign"] = relationship(back_populates="prospects")
    activities: Mapped[list["OutreachActivity"]] = relationship(back_populates="prospect")


class OutreachActivity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outreach_activities"

    prospect_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("outreach_prospects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(40), nullable=False, default="note")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    prospect: Mapped["OutreachProspect"] = relationship(back_populates="activities")


class CampaignJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_jobs"

    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CampaignLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_logs"

    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("campaign_tasks.id", ondelete="SET NULL"), index=True
    )
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info", index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    campaign: Mapped["BacklinkCampaign"] = relationship(back_populates="logs")


class CampaignTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_tasks"

    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("campaign_assets.id", ondelete="SET NULL"), index=True
    )
    group_name: Mapped[str | None] = mapped_column(String(80))
    tier: Mapped[int | None] = mapped_column(Integer)
    task_type: Mapped[str] = mapped_column(String(40), nullable=False, default="generate")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    campaign: Mapped["BacklinkCampaign"] = relationship(back_populates="tasks")


class CampaignMediaUsage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_media_usage"

    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("media_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("campaign_assets.id", ondelete="SET NULL"), index=True
    )
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
