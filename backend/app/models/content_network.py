"""Phase 7 — content network analysis runs and slug redirects."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.public_page import PublicPage


class ContentNetworkRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_network_runs"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    pages_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suggestions_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship()


class PublicSlugRedirect(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "public_slug_redirects"
    __table_args__ = (UniqueConstraint("old_slug", name="uq_public_slug_redirects_old"),)

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    public_page_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("public_pages.id", ondelete="SET NULL"),
        index=True,
    )
    old_slug: Mapped[str] = mapped_column(String(320), nullable=False)
    new_slug: Mapped[str] = mapped_column(String(320), nullable=False, index=True)

    project: Mapped["Project"] = relationship()
    public_page: Mapped["PublicPage | None"] = relationship()
