"""Revision 0006 — Phase 6 public pages."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_public_pages"
down_revision = "0005_parasite_seo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "public_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("parasite_seo_jobs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "content_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "content_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "published_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("slug", sa.String(length=320), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="private"),
        sa.Column("public_url", sa.String(length=2048), nullable=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_public_pages_slug"),
        sa.UniqueConstraint("job_id", name="uq_public_pages_job_id"),
    )
    op.create_index("ix_public_pages_content_id", "public_pages", ["content_id"])
    op.create_index("ix_public_pages_project_id", "public_pages", ["project_id"])
    op.create_index("ix_public_pages_status", "public_pages", ["status"])
    op.create_index("ix_public_pages_visibility", "public_pages", ["visibility"])
    op.create_index("ix_public_pages_published_at", "public_pages", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_public_pages_published_at", table_name="public_pages")
    op.drop_index("ix_public_pages_visibility", table_name="public_pages")
    op.drop_index("ix_public_pages_status", table_name="public_pages")
    op.drop_index("ix_public_pages_project_id", table_name="public_pages")
    op.drop_index("ix_public_pages_content_id", table_name="public_pages")
    op.drop_table("public_pages")
