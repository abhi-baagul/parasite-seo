"""Parasite SEO AI workflow jobs (Phase feature module)."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.content import ContentAsset
    from app.models.project import Project
    from app.models.prompt import Prompt
    from app.models.public_page import PublicPage
    from app.models.user import User


class ParasiteSEOJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "parasite_seo_jobs"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    prompt_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        index=True,
    )
    content_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="SET NULL"),
        index=True,
    )
    original_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    advanced_settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    target_link: Mapped[dict | None] = mapped_column(JSONB)
    requirements: Mapped[dict | None] = mapped_column(JSONB)
    step_state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    current_step: Mapped[str] = mapped_column(String(40), nullable=False, default="input")
    error_message: Mapped[str | None] = mapped_column(Text)
    public_slug: Mapped[str | None] = mapped_column(String(320), index=True)
    public_url: Mapped[str | None] = mapped_column(String(2048))
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    optimize_before: Mapped[str | None] = mapped_column(Text)
    optimize_after: Mapped[str | None] = mapped_column(Text)

    project: Mapped["Project"] = relationship()
    user: Mapped["User"] = relationship()
    prompt: Mapped["Prompt | None"] = relationship()
    content: Mapped["ContentAsset | None"] = relationship()
    public_page: Mapped["PublicPage | None"] = relationship(back_populates="job", uselist=False)
