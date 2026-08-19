"""Ensure newer schema exists even if Alembic has not been applied yet."""

from sqlalchemy import text

from app.db.session import engine

_STATEMENTS = (
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(80)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS organization VARCHAR(200)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(120)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS website VARCHAR(2048)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_prefs JSONB NOT NULL DEFAULT '{}'::jsonb",
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
        source_key VARCHAR(180) NOT NULL,
        kind VARCHAR(32) NOT NULL DEFAULT 'info',
        title VARCHAR(300) NOT NULL,
        body TEXT NOT NULL,
        href VARCHAR(500),
        is_read BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_notifications_user_source UNIQUE (user_id, source_key)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications (is_read)",
    "CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at)",
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
    """,
    "CREATE INDEX IF NOT EXISTS ix_public_page_mirrors_public_page_id ON public_page_mirrors (public_page_id)",
    "CREATE INDEX IF NOT EXISTS ix_public_page_mirrors_provider ON public_page_mirrors (provider)",
    "CREATE INDEX IF NOT EXISTS ix_public_page_mirrors_status ON public_page_mirrors (status)",
)


def ensure_account_schema() -> None:
    with engine.begin() as connection:
        for statement in _STATEMENTS:
            connection.execute(text(statement))
