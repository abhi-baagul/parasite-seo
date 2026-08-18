"""Revision 0009 — Project-aware automatic backlink campaign engine."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_auto_backlink_engine"
down_revision = "0008_backlink_campaigns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "backlink_campaigns",
        sa.Column("parasite_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parasite_seo_jobs.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "backlink_campaigns",
        sa.Column("duplicated_from_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlink_campaigns.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("backlink_campaigns", sa.Column("mock_mode", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("backlink_campaigns", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("backlink_campaigns", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "backlink_campaigns",
        sa.Column("intelligence", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_backlink_campaigns_parasite_job_id", "backlink_campaigns", ["parasite_job_id"])

    op.add_column("campaign_assets", sa.Column("link_group", sa.String(80), nullable=True))
    op.add_column("campaign_assets", sa.Column("relevance_score", sa.Integer(), nullable=True))
    op.add_column("campaign_assets", sa.Column("is_mock", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    op.add_column(
        "publishing_destinations",
        sa.Column("authorization_status", sa.String(40), nullable=False, server_default="authorized"),
    )

    op.add_column("backlinks", sa.Column("link_kind", sa.String(32), nullable=False, server_default="external"))
    op.add_column("backlinks", sa.Column("is_mock", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("backlinks", sa.Column("indexed_status", sa.String(32), nullable=False, server_default="unknown"))

    op.create_table(
        "campaign_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaign_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("group_name", sa.String(80), nullable=True),
        sa.Column("tier", sa.Integer(), nullable=True),
        sa.Column("task_type", sa.String(40), nullable=False, server_default="generate"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_campaign_tasks_campaign_id", "campaign_tasks", ["campaign_id"])
    op.create_index("ix_campaign_tasks_asset_id", "campaign_tasks", ["asset_id"])
    op.create_index("ix_campaign_tasks_status", "campaign_tasks", ["status"])

    op.create_table(
        "campaign_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaign_tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("meta", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_campaign_logs_campaign_id", "campaign_logs", ["campaign_id"])
    op.create_index("ix_campaign_logs_task_id", "campaign_logs", ["task_id"])
    op.create_index("ix_campaign_logs_level", "campaign_logs", ["level"])

    op.create_table(
        "campaign_media_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("media_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaign_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_campaign_media_usage_campaign_id", "campaign_media_usage", ["campaign_id"])
    op.create_index("ix_campaign_media_usage_media_id", "campaign_media_usage", ["media_id"])
    op.create_index("ix_campaign_media_usage_asset_id", "campaign_media_usage", ["asset_id"])


def downgrade() -> None:
    op.drop_table("campaign_media_usage")
    op.drop_table("campaign_logs")
    op.drop_table("campaign_tasks")
    op.drop_column("backlinks", "indexed_status")
    op.drop_column("backlinks", "is_mock")
    op.drop_column("backlinks", "link_kind")
    op.drop_column("publishing_destinations", "authorization_status")
    op.drop_column("campaign_assets", "is_mock")
    op.drop_column("campaign_assets", "relevance_score")
    op.drop_column("campaign_assets", "link_group")
    op.drop_index("ix_backlink_campaigns_parasite_job_id", table_name="backlink_campaigns")
    op.drop_column("backlink_campaigns", "intelligence")
    op.drop_column("backlink_campaigns", "archived_at")
    op.drop_column("backlink_campaigns", "approved_at")
    op.drop_column("backlink_campaigns", "mock_mode")
    op.drop_column("backlink_campaigns", "duplicated_from_id")
    op.drop_column("backlink_campaigns", "parasite_job_id")
