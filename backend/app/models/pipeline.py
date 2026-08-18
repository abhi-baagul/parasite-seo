from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.content import ContentAsset
    from app.models.prompt import Prompt


class PromptAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_analyses"

    prompt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    requirements: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confirmed_requirements: Mapped[dict | None] = mapped_column(JSONB)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uncertain_fields: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    content_asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="SET NULL"),
        index=True,
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="analyses")


class ContentResearchBrief(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_research_briefs"
    __table_args__ = (UniqueConstraint("content_asset_id", "version_number", name="uq_research_content_version"),)

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    source_note: Mapped[str | None] = mapped_column(Text)

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="research_briefs")


class ContentStrategy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_strategies"
    __table_args__ = (UniqueConstraint("content_asset_id", "version_number", name="uq_strategy_content_version"),)

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="strategies")


class ContentOutline(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_outlines"
    __table_args__ = (UniqueConstraint("content_asset_id", "version_number", name="uq_outline_content_version"),)

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="outlines")


class ContentGenerationJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_generation_jobs"

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    error_message: Mapped[str | None] = mapped_column(Text)
    ai_run_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="SET NULL"))

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="generation_jobs")
