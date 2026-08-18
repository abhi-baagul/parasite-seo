from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AnalyticsMetricType

if TYPE_CHECKING:
    from app.models.content import ContentAsset
    from app.models.project import Project


class AnalyticsMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_metrics"
    __table_args__ = (
        Index("ix_analytics_metrics_project_id", "project_id"),
        Index("ix_analytics_metrics_metric_date", "metric_date"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    content_asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="SET NULL"),
        index=True,
    )
    metric_type: Mapped[str] = mapped_column(String(40), nullable=False, default=AnalyticsMetricType.CLICKS.value)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str | None] = mapped_column(String(80))

    project: Mapped["Project"] = relationship(back_populates="analytics_metrics")
    content_asset: Mapped["ContentAsset | None"] = relationship(back_populates="analytics_metrics")
