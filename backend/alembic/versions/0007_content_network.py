"""Revision 0007 — Phase 7 content network + internal link intelligence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_content_network"
down_revision = "0006_public_pages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("link_settings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.add_column(
        "content_links",
        sa.Column("target_content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_assets.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_content_links_target_content_id", "content_links", ["target_content_id"])

    op.add_column(
        "internal_link_suggestions",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True),
    )
    op.add_column("internal_link_suggestions", sa.Column("relevance_score", sa.Integer(), nullable=True))
    op.add_column("internal_link_suggestions", sa.Column("confidence_score", sa.Integer(), nullable=True))
    op.add_column("internal_link_suggestions", sa.Column("placement", sa.String(length=300), nullable=True))
    op.add_column("internal_link_suggestions", sa.Column("context", sa.Text(), nullable=True))
    op.add_column(
        "internal_link_suggestions",
        sa.Column("suggestion_type", sa.String(length=40), nullable=False, server_default="contextual"),
    )
    op.create_index("ix_internal_link_suggestions_project_id", "internal_link_suggestions", ["project_id"])
    op.create_index("ix_internal_link_suggestions_status", "internal_link_suggestions", ["status"])

    op.create_table(
        "content_network_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("pages_analyzed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("suggestions_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("summary", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_content_network_runs_project_id", "content_network_runs", ["project_id"])
    op.create_index("ix_content_network_runs_status", "content_network_runs", ["status"])

    op.create_table(
        "public_slug_redirects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("public_page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public_pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("old_slug", sa.String(length=320), nullable=False),
        sa.Column("new_slug", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("old_slug", name="uq_public_slug_redirects_old"),
    )
    op.create_index("ix_public_slug_redirects_project_id", "public_slug_redirects", ["project_id"])
    op.create_index("ix_public_slug_redirects_public_page_id", "public_slug_redirects", ["public_page_id"])
    op.create_index("ix_public_slug_redirects_new_slug", "public_slug_redirects", ["new_slug"])


def downgrade() -> None:
    op.drop_index("ix_public_slug_redirects_new_slug", table_name="public_slug_redirects")
    op.drop_index("ix_public_slug_redirects_public_page_id", table_name="public_slug_redirects")
    op.drop_index("ix_public_slug_redirects_project_id", table_name="public_slug_redirects")
    op.drop_table("public_slug_redirects")
    op.drop_index("ix_content_network_runs_status", table_name="content_network_runs")
    op.drop_index("ix_content_network_runs_project_id", table_name="content_network_runs")
    op.drop_table("content_network_runs")
    op.drop_index("ix_internal_link_suggestions_status", table_name="internal_link_suggestions")
    op.drop_index("ix_internal_link_suggestions_project_id", table_name="internal_link_suggestions")
    op.drop_column("internal_link_suggestions", "suggestion_type")
    op.drop_column("internal_link_suggestions", "context")
    op.drop_column("internal_link_suggestions", "placement")
    op.drop_column("internal_link_suggestions", "confidence_score")
    op.drop_column("internal_link_suggestions", "relevance_score")
    op.drop_column("internal_link_suggestions", "project_id")
    op.drop_index("ix_content_links_target_content_id", table_name="content_links")
    op.drop_column("content_links", "target_content_id")
    op.drop_column("projects", "link_settings")
