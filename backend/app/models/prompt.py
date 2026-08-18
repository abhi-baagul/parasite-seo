from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PromptStatus

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.content import ContentAsset
    from app.models.pipeline import PromptAnalysis
    from app.models.project import Project


class Prompt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompts"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        index=True,
    )
    raw_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=PromptStatus.DRAFT.value)

    project: Mapped["Project"] = relationship(back_populates="prompts")
    campaign: Mapped["Campaign | None"] = relationship(back_populates="prompts")
    content_assets: Mapped[list["ContentAsset"]] = relationship(back_populates="prompt")
    analyses: Mapped[list["PromptAnalysis"]] = relationship(back_populates="prompt")
