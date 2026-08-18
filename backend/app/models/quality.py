from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import QualityCheckType, QualityStatus

if TYPE_CHECKING:
    from app.models.content import ContentAsset


class QualityCheck(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "quality_checks"

    content_asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    check_type: Mapped[str] = mapped_column(String(40), nullable=False, default=QualityCheckType.QUALITY.value)
    score: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=QualityStatus.PASSED.value)
    issues: Mapped[list | dict] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    recommendations: Mapped[list | dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    content_asset: Mapped["ContentAsset"] = relationship(back_populates="quality_checks")
