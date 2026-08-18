"""Revision 0005 — Parasite SEO AI jobs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_parasite_seo"
down_revision = "0004_content_studio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parasite_seo_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("prompt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("original_prompt", sa.Text(), nullable=False),
        sa.Column("advanced_settings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("target_link", postgresql.JSONB(), nullable=True),
        sa.Column("requirements", postgresql.JSONB(), nullable=True),
        sa.Column("step_state", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("current_step", sa.String(length=40), nullable=False, server_default="input"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("public_slug", sa.String(length=320), nullable=True),
        sa.Column("public_url", sa.String(length=2048), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("optimize_before", sa.Text(), nullable=True),
        sa.Column("optimize_after", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_parasite_seo_jobs_project_id", "parasite_seo_jobs", ["project_id"])
    op.create_index("ix_parasite_seo_jobs_user_id", "parasite_seo_jobs", ["user_id"])
    op.create_index("ix_parasite_seo_jobs_prompt_id", "parasite_seo_jobs", ["prompt_id"])
    op.create_index("ix_parasite_seo_jobs_content_id", "parasite_seo_jobs", ["content_id"])
    op.create_index("ix_parasite_seo_jobs_status", "parasite_seo_jobs", ["status"])
    op.create_index("ix_parasite_seo_jobs_public_slug", "parasite_seo_jobs", ["public_slug"])


def downgrade() -> None:
    op.drop_index("ix_parasite_seo_jobs_public_slug", table_name="parasite_seo_jobs")
    op.drop_index("ix_parasite_seo_jobs_status", table_name="parasite_seo_jobs")
    op.drop_index("ix_parasite_seo_jobs_content_id", table_name="parasite_seo_jobs")
    op.drop_index("ix_parasite_seo_jobs_prompt_id", table_name="parasite_seo_jobs")
    op.drop_index("ix_parasite_seo_jobs_user_id", table_name="parasite_seo_jobs")
    op.drop_index("ix_parasite_seo_jobs_project_id", table_name="parasite_seo_jobs")
    op.drop_table("parasite_seo_jobs")
