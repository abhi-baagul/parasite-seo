"""Initial schema for Parasite SEO foundation tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("niche", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("language", sa.String(length=40), nullable=True),
        sa.Column("target_audience", sa.String(length=255), nullable=True),
        sa.Column("monetization_model", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_projects_user_id",
        "projects",
        ["user_id"],
    )

    # ------------------------------------------------------------------
    # Campaigns
    # ------------------------------------------------------------------
    op.create_table(
        "campaigns",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("target_country", sa.String(length=80), nullable=True),
        sa.Column("language", sa.String(length=40), nullable=True),
        sa.Column(
            "default_content_type",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column("default_word_count", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------
    op.create_table(
        "prompts",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("raw_prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # Content Assets
    # 0002 columns intentionally excluded:
    #   seo_title
    #   meta_description
    #   structured_body
    # ------------------------------------------------------------------
    op.create_table(
        "content_assets",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "prompt_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("slug", sa.String(length=320), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("seo_score", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["prompt_id"],
            ["prompts.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "slug",
            name="uq_content_assets_project_slug",
        ),
    )

    op.create_index(
        "ix_content_assets_project_id",
        "content_assets",
        ["project_id"],
    )
    op.create_index(
        "ix_content_assets_campaign_id",
        "content_assets",
        ["campaign_id"],
    )
    op.create_index(
        "ix_content_assets_prompt_id",
        "content_assets",
        ["prompt_id"],
    )
    op.create_index(
        "ix_content_assets_status",
        "content_assets",
        ["status"],
    )

    # ------------------------------------------------------------------
    # Content Versions
    # 0004 source intentionally excluded.
    # ------------------------------------------------------------------
    op.create_table(
        "content_versions",
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["content_assets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "content_asset_id",
            "version_number",
            name="uq_content_versions_asset_number",
        ),
    )

    op.create_index(
        "ix_content_versions_content_asset_id",
        "content_versions",
        ["content_asset_id"],
    )

    # ------------------------------------------------------------------
    # Content Links
    # 0007 target_content_id intentionally excluded.
    # ------------------------------------------------------------------
    op.create_table(
        "content_links",
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "target_url",
            sa.String(length=2048),
            nullable=False,
        ),
        sa.Column(
            "anchor_text",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "placement_description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "link_attribute",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["content_assets.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "link_attribute IN ('standard', 'sponsored', 'ugc', 'nofollow')",
            name="ck_content_links_attribute",
        ),
    )

    op.create_index(
        "ix_content_links_content_asset_id",
        "content_links",
        ["content_asset_id"],
    )
    op.create_index(
        "ix_content_links_target_url",
        "content_links",
        ["target_url"],
    )

    # ------------------------------------------------------------------
    # Keywords
    # ------------------------------------------------------------------
    op.create_table(
        "keywords",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("keyword_type", sa.String(length=32), nullable=False),
        sa.Column("search_volume", sa.Integer(), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("cpc", sa.Numeric(12, 4), nullable=True),
        sa.Column("intent", sa.String(length=32), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("language", sa.String(length=40), nullable=True),
        sa.Column("opportunity_score", sa.Numeric(8, 2), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["content_assets.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_keywords_keyword",
        "keywords",
        ["keyword"],
    )
    op.create_index(
        "ix_keywords_project_id",
        "keywords",
        ["project_id"],
    )
    op.create_index(
        "ix_keywords_content_asset_id",
        "keywords",
        ["content_asset_id"],
    )

    # ------------------------------------------------------------------
    # Media Assets
    # ------------------------------------------------------------------
    op.create_table(
        "media_assets",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("media_type", sa.String(length=40), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("alt_text", sa.Text(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column(
            "license_information",
            sa.Text(),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["content_assets.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_media_assets_project_id",
        "media_assets",
        ["project_id"],
    )
    op.create_index(
        "ix_media_assets_content_asset_id",
        "media_assets",
        ["content_asset_id"],
    )

    # ------------------------------------------------------------------
    # Quality Checks
    # ------------------------------------------------------------------
    op.create_table(
        "quality_checks",
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("check_type", sa.String(length=40), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "issues",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "recommendations",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["content_assets.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_quality_checks_content_asset_id",
        "quality_checks",
        ["content_asset_id"],
    )

    # ------------------------------------------------------------------
    # AI Runs
    # ------------------------------------------------------------------
    op.create_table(
        "ai_runs",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("agent_type", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column(
            "estimated_cost",
            sa.Numeric(12, 6),
            nullable=False,
        ),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["content_assets.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_ai_runs_project_id",
        "ai_runs",
        ["project_id"],
    )
    op.create_index(
        "ix_ai_runs_content_asset_id",
        "ai_runs",
        ["content_asset_id"],
    )
    op.create_index(
        "ix_ai_runs_status",
        "ai_runs",
        ["status"],
    )

    # ------------------------------------------------------------------
    # Analytics Metrics
    # ------------------------------------------------------------------
    op.create_table(
        "analytics_metrics",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("metric_type", sa.String(length=40), nullable=False),
        sa.Column(
            "metric_value",
            sa.Numeric(16, 4),
            nullable=False,
        ),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["content_assets.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_analytics_metrics_project_id",
        "analytics_metrics",
        ["project_id"],
    )
    op.create_index(
        "ix_analytics_metrics_metric_date",
        "analytics_metrics",
        ["metric_date"],
    )
    op.create_index(
        "ix_analytics_metrics_content_asset_id",
        "analytics_metrics",
        ["content_asset_id"],
    )

    # ------------------------------------------------------------------
    # Publishing Channels
    # ------------------------------------------------------------------
    op.create_table(
        "publishing_channels",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "channel_type",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "configuration",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_publishing_channels_project_id",
        "publishing_channels",
        ["project_id"],
    )

    # ------------------------------------------------------------------
    # Published Assets
    # ------------------------------------------------------------------
    op.create_table(
        "published_assets",
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "publishing_channel_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "published_url",
            sa.String(length=2048),
            nullable=True,
        ),
        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_checked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["content_asset_id"],
            ["content_assets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["publishing_channel_id"],
            ["publishing_channels.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_published_assets_content_asset_id",
        "published_assets",
        ["content_asset_id"],
    )
    op.create_index(
        "ix_published_assets_publishing_channel_id",
        "published_assets",
        ["publishing_channel_id"],
    )
    op.create_index(
        "ix_published_assets_status",
        "published_assets",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_published_assets_status",
        table_name="published_assets",
    )
    op.drop_index(
        "ix_published_assets_publishing_channel_id",
        table_name="published_assets",
    )
    op.drop_index(
        "ix_published_assets_content_asset_id",
        table_name="published_assets",
    )
    op.drop_table("published_assets")

    op.drop_index(
        "ix_publishing_channels_project_id",
        table_name="publishing_channels",
    )
    op.drop_table("publishing_channels")

    op.drop_index(
        "ix_analytics_metrics_content_asset_id",
        table_name="analytics_metrics",
    )
    op.drop_index(
        "ix_analytics_metrics_metric_date",
        table_name="analytics_metrics",
    )
    op.drop_index(
        "ix_analytics_metrics_project_id",
        table_name="analytics_metrics",
    )
    op.drop_table("analytics_metrics")

    op.drop_index(
        "ix_ai_runs_status",
        table_name="ai_runs",
    )
    op.drop_index(
        "ix_ai_runs_content_asset_id",
        table_name="ai_runs",
    )
    op.drop_index(
        "ix_ai_runs_project_id",
        table_name="ai_runs",
    )
    op.drop_table("ai_runs")

    op.drop_index(
        "ix_quality_checks_content_asset_id",
        table_name="quality_checks",
    )
    op.drop_table("quality_checks")

    op.drop_index(
        "ix_media_assets_content_asset_id",
        table_name="media_assets",
    )
    op.drop_index(
        "ix_media_assets_project_id",
        table_name="media_assets",
    )
    op.drop_table("media_assets")

    op.drop_index(
        "ix_keywords_content_asset_id",
        table_name="keywords",
    )
    op.drop_index(
        "ix_keywords_project_id",
        table_name="keywords",
    )
    op.drop_index(
        "ix_keywords_keyword",
        table_name="keywords",
    )
    op.drop_table("keywords")

    op.drop_index(
        "ix_content_links_target_url",
        table_name="content_links",
    )
    op.drop_index(
        "ix_content_links_content_asset_id",
        table_name="content_links",
    )
    op.drop_table("content_links")

    op.drop_index(
        "ix_content_versions_content_asset_id",
        table_name="content_versions",
    )
    op.drop_table("content_versions")

    op.drop_index(
        "ix_content_assets_status",
        table_name="content_assets",
    )
    op.drop_index(
        "ix_content_assets_prompt_id",
        table_name="content_assets",
    )
    op.drop_index(
        "ix_content_assets_campaign_id",
        table_name="content_assets",
    )
    op.drop_index(
        "ix_content_assets_project_id",
        table_name="content_assets",
    )
    op.drop_table("content_assets")

    op.drop_table("prompts")
    op.drop_table("campaigns")

    op.drop_index(
        "ix_projects_user_id",
        table_name="projects",
    )
    op.drop_table("projects")

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )
    op.drop_table("users")
