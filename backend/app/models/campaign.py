from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CampaignStatus, ContentType

if TYPE_CHECKING:
    from app.models.content import ContentAsset
    from app.models.project import Project
    from app.models.prompt import Prompt


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=CampaignStatus.ACTIVE.value)
    target_country: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str | None] = mapped_column(String(40))
    default_content_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=ContentType.ARTICLE.value,
    )
    default_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1200)

    project: Mapped["Project"] = relationship(back_populates="campaigns")
    prompts: Mapped[list["Prompt"]] = relationship(back_populates="campaign")
    content_assets: Mapped[list["ContentAsset"]] = relationship(back_populates="campaign")
