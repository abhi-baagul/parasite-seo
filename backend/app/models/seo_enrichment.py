"""Phase 4 SEO enrichment persistence models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SuggestionStatus

if TYPE_CHECKING:
    from app.models.content import ContentAsset


class ContentMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_metadata"
    __table_args__ = (UniqueConstraint("content_asset_id", name="uq_content_metadata_asset"),)

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seo_title: Mapped[str | None] = mapped_column(String(300))
    meta_description: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str | None] = mapped_column(String(320))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    og_title: Mapped[str | None] = mapped_column(String(300))
    og_description: Mapped[str | None] = mapped_column(Text)
    og_image: Mapped[str | None] = mapped_column(String(2048))
    twitter_title: Mapped[str | None] = mapped_column(String(300))
    twitter_description: Mapped[str | None] = mapped_column(Text)
    title_options: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    meta_options: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="metadata_record")


class ContentTag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_tags"
    __table_args__ = (UniqueConstraint("content_asset_id", "name", name="uq_content_tag_name"),)

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="ai")
    is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="tags")


class ContentCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_categories"
    __table_args__ = (UniqueConstraint("content_asset_id", "name", name="uq_content_category_name"),)

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="ai")
    is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="categories")


class KeywordAnalysisRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "keyword_analyses"

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    content_hash: Mapped[str | None] = mapped_column(String(64))

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="keyword_analyses")


class SEOAnalysisRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seo_analyses"

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    overall_score: Mapped[int | None] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(64))

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="seo_analyses")


class InternalLinkSuggestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "internal_link_suggestions"

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    target_content_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        index=True,
    )
    source_section: Mapped[str | None] = mapped_column(String(300))
    anchor_text: Mapped[str] = mapped_column(String(500), nullable=False)
    target_path: Mapped[str] = mapped_column(String(500), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    relevance_score: Mapped[int | None] = mapped_column(Integer)
    confidence_score: Mapped[int | None] = mapped_column(Integer)
    placement: Mapped[str | None] = mapped_column(String(300))
    context: Mapped[str | None] = mapped_column(Text)
    suggestion_type: Mapped[str] = mapped_column(String(40), nullable=False, default="contextual")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SuggestionStatus.SUGGESTED.value)

    content_asset: Mapped["ContentAsset"] = relationship(
        back_populates="internal_link_suggestions",
        foreign_keys=[content_asset_id],
    )


class ExternalReference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_references"

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    url: Mapped[str | None] = mapped_column(String(2048))
    anchor_suggestion: Mapped[str] = mapped_column(String(500), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False, default="reference")
    requires_verification: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SuggestionStatus.SUGGESTED.value)

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="external_references")


class MediaSuggestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "media_suggestions"

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    media_type: Mapped[str] = mapped_column(String(40), nullable=False, default="image")
    placement: Mapped[str | None] = mapped_column(String(300))
    purpose: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    generation_prompt: Mapped[str | None] = mapped_column(Text)
    alt_text: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    suggested_filename: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SuggestionStatus.SUGGESTED.value)
    embed_url: Mapped[str | None] = mapped_column(String(2048))

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="media_suggestions")
