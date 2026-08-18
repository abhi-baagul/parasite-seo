"""Phase 4 SEO enrichment tables.

Revision ID: 0003_seo_enrichment
Revises: 0002_ai_pipeline
Create Date: 2026-08-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_seo_enrichment"
down_revision: str | None = "0002_ai_pipeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content_metadata (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            seo_title VARCHAR(300),
            meta_description TEXT,
            slug VARCHAR(320),
            canonical_url VARCHAR(2048),
            og_title VARCHAR(300),
            og_description TEXT,
            og_image VARCHAR(2048),
            twitter_title VARCHAR(300),
            twitter_description TEXT,
            title_options JSONB NOT NULL DEFAULT '[]'::jsonb,
            meta_options JSONB NOT NULL DEFAULT '[]'::jsonb,
            CONSTRAINT uq_content_metadata_asset UNIQUE (content_asset_id)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_metadata_content_asset_id ON content_metadata (content_asset_id);")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content_tags (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            name VARCHAR(120) NOT NULL,
            source VARCHAR(32) NOT NULL DEFAULT 'ai',
            is_accepted BOOLEAN NOT NULL DEFAULT TRUE,
            CONSTRAINT uq_content_tag_name UNIQUE (content_asset_id, name)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_tags_content_asset_id ON content_tags (content_asset_id);")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content_categories (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            name VARCHAR(120) NOT NULL,
            source VARCHAR(32) NOT NULL DEFAULT 'ai',
            is_accepted BOOLEAN NOT NULL DEFAULT TRUE,
            CONSTRAINT uq_content_category_name UNIQUE (content_asset_id, name)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_content_categories_content_asset_id ON content_categories (content_asset_id);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS keyword_analyses (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            content_hash VARCHAR(64)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_keyword_analyses_content_asset_id ON keyword_analyses (content_asset_id);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS seo_analyses (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            overall_score INTEGER,
            content_hash VARCHAR(64)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_seo_analyses_content_asset_id ON seo_analyses (content_asset_id);")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS internal_link_suggestions (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            target_content_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            source_section VARCHAR(300),
            anchor_text VARCHAR(500) NOT NULL,
            target_path VARCHAR(500) NOT NULL,
            reason TEXT,
            status VARCHAR(32) NOT NULL DEFAULT 'suggested'
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_internal_link_suggestions_content_asset_id "
        "ON internal_link_suggestions (content_asset_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_internal_link_suggestions_target_content_id "
        "ON internal_link_suggestions (target_content_id);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS external_references (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            url VARCHAR(2048),
            anchor_suggestion VARCHAR(500) NOT NULL,
            reason TEXT,
            source_type VARCHAR(80) NOT NULL DEFAULT 'reference',
            requires_verification BOOLEAN NOT NULL DEFAULT TRUE,
            status VARCHAR(32) NOT NULL DEFAULT 'suggested'
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_external_references_content_asset_id ON external_references (content_asset_id);"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS media_suggestions (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            content_asset_id UUID NOT NULL REFERENCES content_assets(id) ON DELETE RESTRICT,
            media_type VARCHAR(40) NOT NULL DEFAULT 'image',
            placement VARCHAR(300),
            purpose VARCHAR(300),
            description TEXT,
            generation_prompt TEXT,
            alt_text TEXT,
            caption TEXT,
            suggested_filename VARCHAR(255),
            status VARCHAR(32) NOT NULL DEFAULT 'suggested',
            embed_url VARCHAR(2048)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_media_suggestions_content_asset_id ON media_suggestions (content_asset_id);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS media_suggestions;")
    op.execute("DROP TABLE IF EXISTS external_references;")
    op.execute("DROP TABLE IF EXISTS internal_link_suggestions;")
    op.execute("DROP TABLE IF EXISTS seo_analyses;")
    op.execute("DROP TABLE IF EXISTS keyword_analyses;")
    op.execute("DROP TABLE IF EXISTS content_categories;")
    op.execute("DROP TABLE IF EXISTS content_tags;")
    op.execute("DROP TABLE IF EXISTS content_metadata;")
