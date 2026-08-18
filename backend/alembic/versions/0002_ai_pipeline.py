"""Phase 3 pipeline tables and content metadata columns.

Revision ID: 0002_ai_pipeline
Revises: 0001_initial
Create Date: 2026-08-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_ai_pipeline"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE content_assets
        ADD COLUMN IF NOT EXISTS seo_title VARCHAR(300);
        """
    )
    op.execute(
        """
        ALTER TABLE content_assets
        ADD COLUMN IF NOT EXISTS meta_description TEXT;
        """
    )
    op.execute(
        """
        ALTER TABLE content_assets
        ADD COLUMN IF NOT EXISTS structured_body JSONB;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS prompt_analyses (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE RESTRICT,
            requirements JSONB NOT NULL DEFAULT '{}'::jsonb,
            confirmed_requirements JSONB,
            is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
            uncertain_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
            content_asset_id UUID REFERENCES content_assets(id) ON DELETE SET NULL
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompt_analyses_prompt_id ON prompt_analyses (prompt_id);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_prompt_analyses_content_asset_id ON prompt_analyses (content_asset_id);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content_research_briefs (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            version_number INTEGER NOT NULL DEFAULT 1,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            source_note TEXT,
            CONSTRAINT uq_research_content_version UNIQUE (content_asset_id, version_number)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_content_research_briefs_content_asset_id "
        "ON content_research_briefs (content_asset_id);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content_strategies (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            version_number INTEGER NOT NULL DEFAULT 1,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            CONSTRAINT uq_strategy_content_version UNIQUE (content_asset_id, version_number)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_content_strategies_content_asset_id "
        "ON content_strategies (content_asset_id);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content_outlines (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            version_number INTEGER NOT NULL DEFAULT 1,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_approved BOOLEAN NOT NULL DEFAULT FALSE,
            CONSTRAINT uq_outline_content_version UNIQUE (content_asset_id, version_number)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_content_outlines_content_asset_id "
        "ON content_outlines (content_asset_id);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content_generation_jobs (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            stage VARCHAR(40) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'queued',
            error_message TEXT,
            ai_run_id UUID REFERENCES ai_runs(id) ON DELETE SET NULL
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_content_generation_jobs_content_asset_id "
        "ON content_generation_jobs (content_asset_id);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content_generation_jobs;")
    op.execute("DROP TABLE IF EXISTS content_outlines;")
    op.execute("DROP TABLE IF EXISTS content_strategies;")
    op.execute("DROP TABLE IF EXISTS content_research_briefs;")
    op.execute("DROP TABLE IF EXISTS prompt_analyses;")
    op.execute("ALTER TABLE content_assets DROP COLUMN IF EXISTS structured_body;")
    op.execute("ALTER TABLE content_assets DROP COLUMN IF EXISTS meta_description;")
    op.execute("ALTER TABLE content_assets DROP COLUMN IF EXISTS seo_title;")
