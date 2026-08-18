"""Ensure account columns exist even if Alembic 0010 has not been applied yet."""

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
)


def ensure_account_schema() -> None:
    with engine.begin() as connection:
        for statement in _STATEMENTS:
            connection.execute(text(statement))
