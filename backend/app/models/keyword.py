from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import KeywordIntent, KeywordType

if TYPE_CHECKING:
    from app.models.content import ContentAsset
    from app.models.project import Project


class Keyword(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "keywords"
    __table_args__ = (
        Index("ix_keywords_keyword", "keyword"),
        Index("ix_keywords_project_id", "project_id"),
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
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    keyword_type: Mapped[str] = mapped_column(String(32), nullable=False, default=KeywordType.PRIMARY.value)
    search_volume: Mapped[int | None] = mapped_column(Integer)
    difficulty: Mapped[int | None] = mapped_column(Integer)
    cpc: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    intent: Mapped[str | None] = mapped_column(String(32), default=KeywordIntent.INFORMATIONAL.value)
    country: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str | None] = mapped_column(String(40))
    opportunity_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))

    project: Mapped["Project"] = relationship(back_populates="keywords")
    content_asset: Mapped["ContentAsset | None"] = relationship(back_populates="keywords")
