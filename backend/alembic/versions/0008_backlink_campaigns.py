"""Revision 0008 — Phase 8 backlink campaigns."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_backlink_campaigns"
down_revision = "0007_content_network"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_buckets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("niche", sa.String(120), nullable=True),
        sa.Column("topics", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("keywords", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_content_buckets_project_id", "content_buckets", ["project_id"])

    op.create_table(
        "campaign_strategy_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("strategy_type", sa.String(40), nullable=False, server_default="tiered_network"),
        sa.Column("blueprint", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_campaign_strategy_templates_project_id", "campaign_strategy_templates", ["project_id"])

    op.create_table(
        "publishing_destinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("provider_type", sa.String(40), nullable=False, server_default="mock_local"),
        sa.Column("base_url", sa.String(2048), nullable=True),
        sa.Column("configuration", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("credentials_ref", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("test_status", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_publishing_destinations_project_id", "publishing_destinations", ["project_id"])

    op.create_table(
        "backlink_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("strategy_type", sa.String(40), nullable=False, server_default="tiered_network"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("wizard_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("target_url", sa.String(2048), nullable=True),
        sa.Column("target_content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_public_page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public_pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("primary_keyword", sa.String(300), nullable=True),
        sa.Column("secondary_keywords", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("country", sa.String(80), nullable=True),
        sa.Column("language", sa.String(40), nullable=True),
        sa.Column("niche", sa.String(120), nullable=True),
        sa.Column("target_audience", sa.String(255), nullable=True),
        sa.Column("blueprint", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("settings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("disclosure", sa.Text(), nullable=False),
        sa.Column("bucket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_buckets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_backlink_campaigns_project_id", "backlink_campaigns", ["project_id"])
    op.create_index("ix_backlink_campaigns_user_id", "backlink_campaigns", ["user_id"])
    op.create_index("ix_backlink_campaigns_status", "backlink_campaigns", ["status"])
    op.create_index("ix_backlink_campaigns_target_content_id", "backlink_campaigns", ["target_content_id"])
    op.create_index("ix_backlink_campaigns_target_public_page_id", "backlink_campaigns", ["target_public_page_id"])

    op.create_table(
        "campaign_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("master_content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("publishing_destinations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("asset_type", sa.String(40), nullable=False, server_default="tier1"),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("topic", sa.String(300), nullable=True),
        sa.Column("variant_angle", sa.String(300), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("target_url", sa.String(2048), nullable=True),
        sa.Column("parent_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaign_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("anchor_text", sa.String(500), nullable=True),
        sa.Column("link_attribute", sa.String(32), nullable=False, server_default="standard"),
        sa.Column("placement", sa.String(300), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("seo_score", sa.Integer(), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_campaign_assets_campaign_id", "campaign_assets", ["campaign_id"])
    op.create_index("ix_campaign_assets_content_id", "campaign_assets", ["content_id"])
    op.create_index("ix_campaign_assets_tier", "campaign_assets", ["tier"])
    op.create_index("ix_campaign_assets_status", "campaign_assets", ["status"])
    op.create_index("ix_campaign_assets_destination_id", "campaign_assets", ["destination_id"])
    op.create_index("ix_campaign_assets_parent_asset_id", "campaign_assets", ["parent_asset_id"])

    op.create_table(
        "backlinks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaign_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("source_domain", sa.String(255), nullable=False),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("target_content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("anchor_text", sa.String(500), nullable=False),
        sa.Column("attribute", sa.String(32), nullable=False, server_default="standard"),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="cms"),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("campaign_id", "source_url", "target_url", "anchor_text", name="uq_backlinks_campaign_triple"),
    )
    op.create_index("ix_backlinks_campaign_id", "backlinks", ["campaign_id"])
    op.create_index("ix_backlinks_asset_id", "backlinks", ["asset_id"])
    op.create_index("ix_backlinks_source_domain", "backlinks", ["source_domain"])
    op.create_index("ix_backlinks_target_url", "backlinks", ["target_url"])
    op.create_index("ix_backlinks_status", "backlinks", ["status"])
    op.create_index("ix_backlinks_tier", "backlinks", ["tier"])

    op.create_table(
        "backlink_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("backlink_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlinks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("source_ok", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("target_ok", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("anchor_found", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("attribute_match", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_backlink_checks_backlink_id", "backlink_checks", ["backlink_id"])

    op.create_table(
        "outreach_prospects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("website", sa.String(2048), nullable=False),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("topic", sa.String(300), nullable=True),
        sa.Column("relevance_score", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="prospect"),
        sa.Column("draft_subject", sa.String(500), nullable=True),
        sa.Column("draft_body", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_outreach_prospects_campaign_id", "outreach_prospects", ["campaign_id"])
    op.create_index("ix_outreach_prospects_status", "outreach_prospects", ["status"])

    op.create_table(
        "outreach_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outreach_prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_type", sa.String(40), nullable=False, server_default="note"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("meta", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_outreach_activities_prospect_id", "outreach_activities", ["prospect_id"])

    op.create_table(
        "campaign_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("backlink_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_campaign_jobs_campaign_id", "campaign_jobs", ["campaign_id"])
    op.create_index("ix_campaign_jobs_job_type", "campaign_jobs", ["job_type"])
    op.create_index("ix_campaign_jobs_status", "campaign_jobs", ["status"])


def downgrade() -> None:
    for table in (
        "campaign_jobs",
        "outreach_activities",
        "outreach_prospects",
        "backlink_checks",
        "backlinks",
        "campaign_assets",
        "backlink_campaigns",
        "publishing_destinations",
        "campaign_strategy_templates",
        "content_buckets",
    ):
        op.drop_table(table)
