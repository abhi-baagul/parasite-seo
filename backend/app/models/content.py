from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ContentStatus, ContentType, LinkAttribute, LinkStatus

if TYPE_CHECKING:
    from app.models.ai_run import AIRun
    from app.models.analytics import AnalyticsMetric
    from app.models.campaign import Campaign
    from app.models.keyword import Keyword
    from app.models.media import MediaAsset
    from app.models.pipeline import (
        ContentGenerationJob,
        ContentOutline,
        ContentResearchBrief,
        ContentStrategy,
    )
    from app.models.project import Project
    from app.models.prompt import Prompt
    from app.models.publishing import PublishedAsset
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


class ContentAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_assets"
    __table_args__ = (
        Index("ix_content_assets_status", "status"),
        UniqueConstraint("project_id", "slug", name="uq_content_assets_project_slug"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        index=True,
    )
    prompt_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(320), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    seo_title: Mapped[str | None] = mapped_column(String(300))
    meta_description: Mapped[str | None] = mapped_column(Text)
    structured_body: Mapped[dict | None] = mapped_column(JSONB)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False, default=ContentType.ARTICLE.value)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ContentStatus.DRAFT.value)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seo_score: Mapped[int | None] = mapped_column(Integer)
    quality_score: Mapped[int | None] = mapped_column(Integer)

    project: Mapped["Project"] = relationship(back_populates="content_assets")
    campaign: Mapped["Campaign | None"] = relationship(back_populates="content_assets")
    prompt: Mapped["Prompt | None"] = relationship(back_populates="content_assets")
    versions: Mapped[list["ContentVersion"]] = relationship(back_populates="content_asset")
    links: Mapped[list["ContentLink"]] = relationship(
        back_populates="content_asset",
        foreign_keys="ContentLink.content_asset_id",
    )
    media_assets: Mapped[list["MediaAsset"]] = relationship(back_populates="content_asset")
    quality_checks: Mapped[list["QualityCheck"]] = relationship(back_populates="content_asset")
    ai_runs: Mapped[list["AIRun"]] = relationship(back_populates="content_asset")
    published_assets: Mapped[list["PublishedAsset"]] = relationship(back_populates="content_asset")
    keywords: Mapped[list["Keyword"]] = relationship(back_populates="content_asset")
    analytics_metrics: Mapped[list["AnalyticsMetric"]] = relationship(back_populates="content_asset")
    research_briefs: Mapped[list["ContentResearchBrief"]] = relationship(back_populates="content_asset")
    strategies: Mapped[list["ContentStrategy"]] = relationship(back_populates="content_asset")
    outlines: Mapped[list["ContentOutline"]] = relationship(back_populates="content_asset")
    generation_jobs: Mapped[list["ContentGenerationJob"]] = relationship(back_populates="content_asset")
    metadata_record: Mapped["ContentMetadata | None"] = relationship(
        back_populates="content_asset", uselist=False
    )
    tags: Mapped[list["ContentTag"]] = relationship(back_populates="content_asset")
    categories: Mapped[list["ContentCategory"]] = relationship(back_populates="content_asset")
    keyword_analyses: Mapped[list["KeywordAnalysisRecord"]] = relationship(back_populates="content_asset")
    seo_analyses: Mapped[list["SEOAnalysisRecord"]] = relationship(back_populates="content_asset")
    internal_link_suggestions: Mapped[list["InternalLinkSuggestion"]] = relationship(
        back_populates="content_asset",
        foreign_keys="InternalLinkSuggestion.content_asset_id",
    )
    external_references: Mapped[list["ExternalReference"]] = relationship(back_populates="content_asset")
    media_suggestions: Mapped[list["MediaSuggestion"]] = relationship(back_populates="content_asset")


class ContentVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "content_versions"
    __table_args__ = (
        UniqueConstraint("content_asset_id", "version_number", name="uq_content_versions_asset_number"),
        Index("ix_content_versions_content_asset_id", "content_asset_id"),
    )

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="versions")
    author: Mapped["User | None"] = relationship()


class ContentLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_links"
    __table_args__ = (
        Index("ix_content_links_content_asset_id", "content_asset_id"),
        Index("ix_content_links_target_url", "target_url"),
        CheckConstraint(
            "link_attribute IN ('standard', 'sponsored', 'ugc', 'nofollow')",
            name="ck_content_links_attribute",
        ),
    )

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    target_content_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="SET NULL"),
        index=True,
    )
    anchor_text: Mapped[str] = mapped_column(String(500), nullable=False)
    placement_description: Mapped[str | None] = mapped_column(Text)
    link_attribute: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=LinkAttribute.STANDARD.value,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=LinkStatus.PLANNED.value)

    content_asset: Mapped["ContentAsset"] = relationship(
        back_populates="links",
        foreign_keys=[content_asset_id],
    )
