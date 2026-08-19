"""Revision 0011 — Public page cloud mirrors."""

from alembic import op

revision = "0011_public_page_mirrors"
down_revision = "0010_user_profile_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public_page_mirrors (
            id UUID PRIMARY KEY,
            public_page_id UUID NOT NULL REFERENCES public_pages (id) ON DELETE CASCADE,
            provider VARCHAR(40) NOT NULL,
            label VARCHAR(120) NOT NULL,
            vanity_slug VARCHAR(320) NOT NULL,
            live_url VARCHAR(2048) NOT NULL,
            display_host VARCHAR(320) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'live',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_public_page_mirrors_page_provider UNIQUE (public_page_id, provider)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_public_page_mirrors_public_page_id ON public_page_mirrors (public_page_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_public_page_mirrors_provider ON public_page_mirrors (provider)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_public_page_mirrors_status ON public_page_mirrors (status)")


def downgrade() -> None:
    op.drop_index("ix_public_page_mirrors_status", table_name="public_page_mirrors")
    op.drop_index("ix_public_page_mirrors_provider", table_name="public_page_mirrors")
    op.drop_index("ix_public_page_mirrors_public_page_id", table_name="public_page_mirrors")
    op.drop_table("public_page_mirrors")
