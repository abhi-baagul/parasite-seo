"""Revision 0004 — Phase 5 Content Studio (version source + asset files)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_content_studio"
down_revision = "0003_seo_enrichment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_versions",
        sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"),
    )
    op.create_table(
        "content_asset_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("content_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("asset_type", sa.String(length=40), nullable=False, server_default="export"),
        sa.Column("mime_type", sa.String(length=120), nullable=False, server_default="application/octet-stream"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_content_asset_files_project_id", "content_asset_files", ["project_id"])
    op.create_index("ix_content_asset_files_content_asset_id", "content_asset_files", ["content_asset_id"])


def downgrade() -> None:
    op.drop_index("ix_content_asset_files_content_asset_id", table_name="content_asset_files")
    op.drop_index("ix_content_asset_files_project_id", table_name="content_asset_files")
    op.drop_table("content_asset_files")
    op.drop_column("content_versions", "source")
