"""Phase 6 — public web pages with permanent shareable URLs."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.content import ContentAsset, ContentVersion
    from app.models.parasite_seo import ParasiteSEOJob
    from app.models.project import Project


class PublicPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "public_pages"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_public_pages_slug"),
        UniqueConstraint("job_id", name="uq_public_pages_job_id"),
        Index("ix_public_pages_content_id", "content_id"),
        Index("ix_public_pages_project_id", "project_id"),
        Index("ix_public_pages_status", "status"),
        Index("ix_public_pages_visibility", "visibility"),
        Index("ix_public_pages_published_at", "published_at"),
    )

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("parasite_seo_jobs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    content_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    content_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_versions.id", ondelete="SET NULL"),
    )
    published_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_versions.id", ondelete="SET NULL"),
    )
    slug: Mapped[str] = mapped_column(String(320), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="private")
    public_url: Mapped[str | None] = mapped_column(String(2048))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    job: Mapped["ParasiteSEOJob"] = relationship(back_populates="public_page")
    content: Mapped["ContentAsset"] = relationship()
    project: Mapped["Project"] = relationship()
    content_version: Mapped["ContentVersion | None"] = relationship(
        foreign_keys=[content_version_id],
    )
    published_version: Mapped["ContentVersion | None"] = relationship(
        foreign_keys=[published_version_id],
    )
