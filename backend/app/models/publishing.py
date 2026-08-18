from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ChannelType, PublishStatus

if TYPE_CHECKING:
    from app.models.content import ContentAsset
    from app.models.project import Project


class PublishingChannel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publishing_channels"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(40), nullable=False, default=ChannelType.CUSTOM.value)
    configuration: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    project: Mapped["Project"] = relationship(back_populates="publishing_channels")
    published_assets: Mapped[list["PublishedAsset"]] = relationship(back_populates="publishing_channel")


class PublishedAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "published_assets"
    __table_args__ = (Index("ix_published_assets_status", "status"),)

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    publishing_channel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("publishing_channels.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    published_url: Mapped[str | None] = mapped_column(String(2048))
    external_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=PublishStatus.DRAFT.value)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="published_assets")
    publishing_channel: Mapped["PublishingChannel"] = relationship(back_populates="published_assets")
