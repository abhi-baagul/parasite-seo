from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ProjectStatus

if TYPE_CHECKING:
    from app.models.ai_run import AIRun
    from app.models.analytics import AnalyticsMetric
    from app.models.campaign import Campaign
    from app.models.content import ContentAsset
    from app.models.keyword import Keyword
    from app.models.media import MediaAsset
    from app.models.prompt import Prompt
    from app.models.publishing import PublishingChannel
    from app.models.user import User


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    niche: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str | None] = mapped_column(String(40))
    target_audience: Mapped[str | None] = mapped_column(String(255))
    monetization_model: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ProjectStatus.ACTIVE.value)
    link_settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship(back_populates="projects")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="project")
    prompts: Mapped[list["Prompt"]] = relationship(back_populates="project")
    content_assets: Mapped[list["ContentAsset"]] = relationship(back_populates="project")
    keywords: Mapped[list["Keyword"]] = relationship(back_populates="project")
    publishing_channels: Mapped[list["PublishingChannel"]] = relationship(back_populates="project")
    analytics_metrics: Mapped[list["AnalyticsMetric"]] = relationship(back_populates="project")
    media_assets: Mapped[list["MediaAsset"]] = relationship(back_populates="project")
    ai_runs: Mapped[list["AIRun"]] = relationship(back_populates="project")
